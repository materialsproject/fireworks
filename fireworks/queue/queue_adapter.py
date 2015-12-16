# coding: utf-8

from __future__ import unicode_literals

"""
This module contains contracts for defining adapters to various queueing systems, e.g. PBS/SLURM/SGE.
"""
import os
import shlex
import string
import subprocess
import threading
import traceback
import abc
import collections
from fireworks.utilities.fw_serializers import FWSerializable, serialize_fw
from fireworks.utilities.fw_utilities import get_fw_logger

__author__ = 'Anubhav Jain'
__credits__ = 'Shyue Ping Ong'
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

                # Python3 - need to convert string to bytes
                if isinstance(self.output, bytes):
                    self.output = self.output.decode("utf-8")
                if isinstance(self.error, bytes):
                    self.error = self.error.decode("utf-8")
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


class QueueAdapterBase(collections.defaultdict, FWSerializable):
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
            subs_dict = {k: v for k, v in self.items()
                         if v is not None}  # clean null values

            for k, v in self.defaults.items():
                subs_dict.setdefault(k, v)

            subs_dict['job_name'] = subs_dict.get('job_name', 'FW_job')

            launch_dir = os.path.abspath(launch_dir)
            subs_dict['launch_dir'] = launch_dir

            # might contain unused parameters as leftover $$
            unclean_template = a.safe_substitute(subs_dict)

            clean_template = filter(lambda l: "$$" not in l,
                                    unclean_template.split('\n'))

            return '\n'.join(clean_template)

    @abc.abstractmethod
    def submit_to_queue(self, script_file):
        """
        submits the job to the queue and returns the job id

        :param script_file: (str) name of the script file to use (String)
        :return: (int) job_id
        """
        pass

    @abc.abstractmethod
    def get_njobs_in_queue(self, username=None):
        """
        returns the number of jobs currently in the queue for the user

        :param username: (str) the username of the jobs to count (default is to autodetect)
        :return: (int) number of jobs in the queue
        """
        pass

    @serialize_fw
    def to_dict(self):
        return dict(self)

    @classmethod
    def from_dict(cls, m_dict):
        return cls(m_dict)

    def get_qlogger(self, name):
        if 'logdir' in self:
            return get_fw_logger(name, self['logdir'])
        else:
            return get_fw_logger(name, stream_level='CRITICAL')


class QScriptTemplate(string.Template):
    delimiter = '$$'
