#!/usr/bin/env python

"""
This module contains contracts for defining adapters to various queueing systems, e.g. PBS/SLURM/SGE.
"""
import getpass

import os
import shlex
import string
import subprocess
import threading
import traceback
from fireworks.utilities.fw_serializers import FWSerializable, serialize_fw
from fireworks.utilities.fw_utilities import get_fw_logger, log_exception, log_fancy

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 28, 2013'


class Command(object):
    """
    Helper class -  run subprocess commands in a different thread with TIMEOUT option.
    From https://gist.github.com/kirpit/1306188
    Based on jcollado's solution:
    http://stackoverflow.com/questions/1191374/subprocess-with-timeout/4825933#4825933
    """
    command = None
    process = None
    status = None
    output, error = '', ''

    def __init__(self, command):
        """
        initialize the object
        :param command: command to run
        """
        if isinstance(command, basestring):
            command = shlex.split(command)
        self.command = command

    def run(self, timeout=None, **kwargs):
        """
        Run the command
        :param timeout: (float) timeout
        :param kwargs:
        :return: (status, output, error)
        """
        def target(**kwargs):
            try:
                self.process = subprocess.Popen(self.command, **kwargs)
                self.output, self.error = self.process.communicate()
                self.status = self.process.returncode
            except:
                self.error = traceback.format_exc()
                self.status = -1
        # default stdout and stderr
        if 'stdout' not in kwargs:
            kwargs['stdout'] = subprocess.PIPE
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.PIPE
        # thread
        thread = threading.Thread(target=target, kwargs=kwargs)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            thread.join()
        return self.status, self.output, self.error


class QueueAdapterBase(dict, FWSerializable):
    """
    The QueueAdapter is responsible for all interactions with a specific \
    queue management system. This includes handling all details of queue \
    script format as well as queue submission and management.

    A user should extend this class with implementations that work on \
    specific queue systems. Examples and implementations are in: \
    fireworks/user_objects/queue_adapters.

    Documentation on implementing queue adapters can be found on FireWorks \
    home page, http://pythonhosted.org/FireWorks
    """

    _fw_name = 'QueueAdapterBase'
    template_file = 'OVERRIDE_ME'  # path to template file for a queue script
    submit_cmd = 'OVERRIDE_ME'  # command to submit jobs, e.g. "qsub" or "squeue"
    q_name = 'OVERRIDE_ME'  # (arbitrary) name, e.g. "pbs" or "slurm"
    defaults = {}  # default parameter values for template

    def parse_jobid(self, output_str):
        """
        After running submit_cmd, parses the job id from the standard output
        :param output_str: Standard output after running submit_cmd
        :return: (int) job id
        """
        raise NotImplementedError('parse_jobid() not implemented for this queueadapter!')

    def get_status_cmd(self, username):
        """
        Get the command (e.g. ["qstat"]) for getting the number of jobs from a user
        :param username: username we want to get the njobs for
        :return: ([str]) command as String[] for subprocess
        """
        raise NotImplementedError('get_status_cmd() not implemented for this queueadapter!')

    def parse_njobs(self, output_str, username):
        """
        Parse the number of jobs in the queue from status_cmd output
        :param output_str: the output string from running the status command, e.g. "qstat" output
        :param username: username we want to get njobs for
        :return: (int) number of jobs in queue
        """
        raise NotImplementedError('parse_njobs() not implemented for this queueadapter!')

    def get_script_str(self, launch_dir):
        """
        returns a (multi-line) String representing the queue script, e.g. PBS script. \
        Uses the template_file along with internal parameters to create the script.

        :param launch_dir: (str) The directory the job will be launched in
        :return: (str) the queue script
        """
        with open(self.template_file) as f:
            a = QScriptTemplate(f.read())

            # set substitution dict for replacements into the template
            subs_dict = dict([(k,v) for k,v in dict(self).iteritems() if v is not None])  # clean null values

            for k, v in self.defaults.iteritems():
                subs_dict[k] = subs_dict.get(k, v)

            subs_dict['job_name'] = subs_dict.get('job_name', 'FW_job')

            launch_dir = os.path.abspath(launch_dir)
            subs_dict['launch_dir'] = launch_dir

            unclean_template = a.safe_substitute(subs_dict)  # might contain unused parameters as leftover $$

            clean_template = []

            for line in unclean_template.split('\n'):
                if '$$' not in line:
                    clean_template.append(line)

            return '\n'.join(clean_template)

    def submit_to_queue(self, script_file):
        """
        submits the job to the queue and returns the job id

        :param script_file: (str) name of the script file to use (String)
        :return: (int) job_id
        """
        if not os.path.exists(script_file):
            raise ValueError('Cannot find script file located at: {}'.format(script_file))

        queue_logger = self.get_qlogger('qadapter.{}'.format(self.q_name))

        # submit the job
        try:
            cmd = [self.submit_cmd, script_file]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.wait()

            # grab the returncode. PBS returns 0 if the job was successful
            if p.returncode == 0:
                try:
                    job_id = self.parse_jobid(p.stdout.read())
                    queue_logger.info('Job submission was successful and job_id is {}'.format(job_id))
                    return job_id
                except:
                    # probably error parsing job code
                    log_exception(queue_logger, 'Could not parse job id following {}...'.format(self.submit_cmd))

            else:
                # some qsub error, e.g. maybe wrong queue specified, don't have permission to submit, etc...
                msgs = [
                    'Error in job submission with {n} file {f} and cmd {c}'.format(n=self.q_name, f=script_file, c=cmd),
                    'The error response reads: {}'.format(p.stderr.read())]
                log_fancy(queue_logger, msgs, 'error')

        except:
            # random error, e.g. no qsub on machine!
            log_exception(queue_logger, 'Running the command: {} caused an error...'.format(self.submit_cmd))

    def get_njobs_in_queue(self, username=None):
        """
        returns the number of jobs currently in the queu efor the user

        :param username: (str) the username of the jobs to count (default is to autodetect)
        :return: (int) number of jobs in the queue
        """
        queue_logger = self.get_qlogger('qadapter.{}'.format(self.q_name))

        # initialize username
        if username is None:
            username = getpass.getuser()

        # run qstat
        qstat = Command(self.get_status_cmd(username))
        p = qstat.run(timeout=5)

        # parse the result
        if p[0] == 0:
            njobs = self.parse_njobs(p[1], username)
            queue_logger.info('The number of jobs currently in the queue is: {}'.format(njobs))
            return njobs

        # there's a problem talking to qstat server?
        msgs = ['Error trying to get the number of jobs in the queue',
                'The error response reads: {}'.format(p[2])]
        log_fancy(queue_logger, msgs, 'error')
        return None

    def __getitem__(self, key):
        """
        Reproduce a simple defaultdict-like behavior - any unset parameters return None
        """
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return None

    @serialize_fw
    def to_dict(self):
        return dict(self)

    @classmethod
    def from_dict(cls, m_dict):
        return cls(m_dict)

    def get_qlogger(self, name):
        if self['logdir']:
            return get_fw_logger(name, self['logdir'])
        else:
            return get_fw_logger(name, stream_level='CRITICAL')


class QScriptTemplate(string.Template):
    delimiter = '$$'