#!/usr/bin/env python

"""
TODO: add docs!
"""

import os
import shlex
import subprocess
import getpass
import threading
import traceback
from fireworks.queue.queue_adapter import QueueAdapterBase
from fireworks.utilities.fw_utilities import log_fancy, log_exception


__author__ = 'Anubhav Jain, Michael Kocher'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'


class Command(object):
    """
    From https://gist.github.com/kirpit/1306188

    Enables to run subprocess commands in a different thread with TIMEOUT option.

    Based on jcollado's solution:
    http://stackoverflow.com/questions/1191374/subprocess-with-timeout/4825933#4825933
    """
    command = None
    process = None
    status = None
    output, error = '', ''

    def __init__(self, command):
        if isinstance(command, basestring):
            command = shlex.split(command)
        self.command = command

    def run(self, timeout=None, **kwargs):
        """ Run a command then return: (status, output, error). """
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


class PBSAdapterNERSC(QueueAdapterBase):
    _fw_name = 'PBSAdapter (NERSC)'
    template_file = os.path.join(os.path.dirname(__file__), 'PBS_template.txt')
    defaults = {}

    def submit_to_queue(self, script_file):

        if not os.path.exists(script_file):
            raise ValueError('Cannot find script file located at: {}'.format(script_file))

        pbs_logger = self.get_qlogger('qadapter.pbs')

        # submit the job
        try:
            cmd = ['qsub', script_file]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.wait()

            # grab the returncode. PBS returns 0 if the job was successful
            if p.returncode == 0:
                try:
                    # output should of the form '2561553.sdb' or '352353.jessup' - just grab the first part for job id
                    job_id = int(p.stdout.read().split('.')[0])
                    pbs_logger.info('Job submission was successful and job_id is {}'.format(job_id))
                    return job_id
                except:
                    # probably error parsing job code
                    log_exception(pbs_logger, 'Could not parse job id following qsub...')

            else:
                # some qsub error, e.g. maybe wrong queue specified, don't have permission to submit, etc...
                msgs = [
                    'Error in job submission with PBS file {f} and cmd {c}'.format(f=script_file,
                                                                                   c=cmd),
                    'The error response reads: {}'.format(p.stderr.read())]
                log_fancy(pbs_logger, 'error', msgs)

        except:
            # random error, e.g. no qsub on machine!
            log_exception(pbs_logger, 'Running qsub caused an error...')

    def get_njobs_in_queue(self, username=None):
        pbs_logger = self.get_qlogger('qadapter.pbs')

        # initialize username
        if username is None:
            username = getpass.getuser()

        # run qstat
        qstat = Command(['qstat', '-a', '-u', username])
        p = qstat.run(timeout=5)

        # parse the result
        if p[0] == 0:
            # lines should have this form
            # '1339044.sdb          username  queuename    2012-02-29-16-43  20460   --   --    --  00:20 C 00:09'
            # count lines that include the username in it

            # TODO: only count running or queued jobs. or rather, *don't* count jobs that are 'C'.
            outs = p[1].split('\n')
            njobs = len([line.split() for line in outs if username in line])
            pbs_logger.info('The number of jobs currently in the queue is: {}'.format(njobs))
            return njobs

        # there's a problem talking to qstat server?
        msgs = ['Error trying to get the number of jobs in the queue using qstat service',
                'The error response reads: {}'.format(p[2])]
        log_fancy(pbs_logger, 'error', msgs)
        return None