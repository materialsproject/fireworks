#!/usr/bin/env python

"""
TODO: add docs!
"""

import os
import subprocess
import getpass
from fireworks.queue.queue_adapter import QueueAdapterBase
from fireworks.utilities.fw_utilities import log_fancy, log_exception


__author__ = 'David Waroquiers, Anubhav Jain, Michael Kocher'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'David Waroquiers'
__email__ = 'david.waroquiers@uclouvain.be'
__date__ = 'Dec 12, 2012'


class SLURMAdapterUCL(QueueAdapterBase):
    _fw_name = 'SLURMAdapter (UCL)'
    template_file = os.path.join(os.path.dirname(__file__), 'SLURM_template.txt')
    defaults = {'ntasks': 1, 'cpus_per_task': 1}

    def submit_to_queue(self, script_file):
        if not os.path.exists(script_file):
            raise ValueError('Cannot find script file located at: {}'.format(script_file))

        slurm_logger = self.get_qlogger('qadapter.slurm')

        # submit the job
        try:
            cmd = ['sbatch', script_file]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.wait()

            # grab the returncode. SLURM returns 0 if the job was successful
            if p.returncode == 0:
                try:
                    # output should of the form '2561553.sdb' or '352353.jessup' - just grab the first part for job id
                    job_id = int(p.stdout.read().split()[3])
                    slurm_logger.info('Job submission was successful and job_id is {}'.format(job_id))
                    return job_id
                except:
                    # probably error parsing job code
                    log_exception(slurm_logger, 'Could not parse job id following slurm...')

            else:
                # some qsub error, e.g. maybe wrong queue specified, don't have permission to submit, etc...
                msgs = ['Error in job submission with SLURM file {f} and cmd {c}'.format(f=script_file, c=cmd),
                        'The error response reads: {}'.format(p.stderr.read())]
                log_fancy(slurm_logger, msgs, 'error')

        except:
            # random error, e.g. no qsub on machine!
            log_exception(slurm_logger, 'Running slurm caused an error...')

    def get_njobs_in_queue(self, username=None):
        slurm_logger = self.get_qlogger('qadapter.slurm')

        if username is None:
            username = getpass.getuser()

        cmd = ['squeue', '-o "%u"', '-u', username]
        p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
        p.wait()

        # parse the result
        if p.returncode == 0:
            # lines should have this form
            # username
            # count lines that include the username in it

            outs = p.stdout.readlines()
            njobs = len([line.split() for line in outs if username in line])
            slurm_logger.info('The number of jobs currently in the queue is: {}'.format(njobs))
            return njobs

        # there's a problem talking to squeue server?
        msgs = ['Error trying to get the number of jobs in the queue using squeue service',
                'The error response reads: {}'.format(p.stderr.read())]
        log_fancy(slurm_logger, msgs, 'error')
        return None