#!/usr/bin/env python

"""
TODO: add docs!
"""

import os
import subprocess
import getpass
import re
from fireworks.queue.queue_adapter import QueueAdapterBase
from fireworks.utilities.fw_utilities import get_fw_logger, \
    log_fancy, log_exception


__author__ = 'David Waroquiers, Anubhav Jain, Michael Kocher'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'David Waroquiers'
__email__ = 'david.waroquiers@uclouvain.be'
__date__ = 'Dec 12, 2012'


class SLURMAdapterUCL(QueueAdapterBase):
    _fw_name = 'SLURMAdapter (UCL)'

    def get_script_str(self, queue_params, launch_dir):
        """
        Create a UCL-style SLURM script. For more documentation, see parent object.
        
        Supported QueueParams.params are:
            - ntasks: number of tasks (default : 1)
            - ntasks_per_node: maximum number of tasks to be invoked for each node
            - cpus_per_task: number of cpus per task (default : 1)
            - walltime: looks like "hh:mm:ss"
            - queue: the queue to run on
            - account: the account to charge 
            - slurm_options: a dict that sets the SLURM -l key-value pairs
            - slurm_tags: a list of SLURM tags
            - job_name: the name of the job to run
            - modules: a list of modules to load
            - exe: the executable to run, after moving to the launch_dir
        """
        # convert launch_dir to absolute path
        launch_dir = os.path.abspath(launch_dir)

        p = queue_params.params

        outs = []
        outs.append('#!/bin/bash')
        outs.append('')

        outs.append('#SBATCH --ntasks={}'.format(p.get('ntasks',1)))

        if p.get('ntasks-per-node', None):
            outs.append('#SBATCH --ntasks-per-node={}'.format(p['ntasks-per-node']))

        outs.append('#SBATCH --cpus-per-task={}'.format(p.get('cpus-per-task',1)))

        if p.get('walltime', None):
            outs.append('#SBATCH --time={}'.format(p['walltime']))

        if p.get('queue', None):
            outs.append('#SBATCH --partition={}'.format(p['queue']))

        if p.get('account', None):
            outs.append('#SBATCH --account={}'.format(p['account']))

        for k, v in p.get('slurm_options', {}).items():
            outs.append('#SBATCH --{k}={v}'.format(k=k, v=v))

        for tag in p.get('slurm_tags', []):
            outs.append('#SBATCH --{}'.format(tag))

        job_name = 'FW_job'
        if p.get('jobname', None):
            job_name = p['jobname']
        outs.append('#SBATCH --job-name={}'.format(job_name))
        outs.append('#SBATCH --output={}'.format(job_name + '-%j.out'))
        outs.append('#SBATCH --error={}'.format(job_name + '-%j.error'))

        outs.append('')
        outs.append('# loading modules')
        for m in p.get('modules', []):
            outs.append('module load {m}'.format(m=m))

        outs.append('')
        outs.append('# moving to working directory')
        outs.append('cd {}'.format(launch_dir))
        outs.append('')

        outs.append('# running executable')
        if p.get('exe', None):
            outs.append(p['exe'])

        outs.append('')
        outs.append('# {f} completed writing Template'.format(f=self.__class__.__name__))
        outs.append('')
        return '\n'.join(outs)

    def submit_to_queue(self, queue_params, script_file):
        """
        for documentation, see parent object
        """

        if not os.path.exists(script_file):
            raise ValueError('Cannot find script file located at: {}'.format(script_file))

        # initialize logger
        slurm_logger = get_fw_logger('rocket.slurm', queue_params.logging_dir)

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
                msgs = ['Error in job submission with SLURM file {f} and cmd {c}'.format(f=script_file, c=cmd)]
                msgs.append('The error response reads: {}'.format(p.stderr.read()))
                log_fancy(slurm_logger, 'error', msgs)

        except:
            # random error, e.g. no qsub on machine!
            log_exception(slurm_logger, 'Running slurm caused an error...')

    def get_njobs_in_queue(self, queue_params, username=None):
        """
        for documentation, see parent object
        """

        # TODO: (low-priority) parse the qstat -x output as an alternate way to get this working
        # tmp_file_name = 'tmp_qstat.xml'
        # cmd = ['qstat', '-x']\n

        # initialize logger
        slurm_logger = get_fw_logger('rocket.slurm', queue_params.logging_dir)

        # initialize username
        if username is None:
            username = getpass.getuser()

        # run qstat
        cmd = ['squeue', '-o "%u"', '-u', username]
        p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
        p.wait()

        # parse the result
        if p.returncode == 0:
            # lines should have this form
            # username
            # count lines that include the username in it

            outs = p.stdout.readlines()
            rx = re.compile(username)
            njobs = len([line.split() for line in outs if rx.search(line) is not None])
            slurm_logger.info('The number of jobs currently in the queue is: {}'.format(njobs))
            return njobs

        # there's a problem talking to qstat server?
        msgs = ['Error trying to get the number of jobs in the queue using squeue service']
        msgs.append('The error response reads: {}'.format(p.stderr.read()))
        log_fancy(slurm_logger, 'error', msgs)
        return None
