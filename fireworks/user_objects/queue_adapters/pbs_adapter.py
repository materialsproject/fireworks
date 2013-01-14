#!/usr/bin/env python

'''
TODO: add docs!
'''

from fireworks.core.queue_adapter_base import QueueAdapterBase
import os
import subprocess
import getpass
import re
from fireworks.utilities.fw_utilities import get_fw_logger,\
    log_fancy, log_exception


__author__ = "Anubhav Jain, Michael Kocher"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Dec 12, 2012"


class PBSAdapterNERSC(QueueAdapterBase):
    
    _fw_name = 'PBSAdapter (NERSC)'
    
    def get_script_str(self, launch_dir, job_parameters):
        '''
        Create a NERSC-style PBS script.
        
        Supported JobParameters.params are:
            - ncores: number of cores
            - walltime: looks like "hh:mm:ss"
            - queue: the queue to run on
            - account: the account to charge 
            - pbs_options: a dict that sets the PBS -l key-value pairs
            - pbs_tags: a list of PBS tags
            - job_name: the name of the job to run
            - modules: a list of modules to load
            - exe: the executable to run, after moving to the launch_dir
        
        :param launch_dir: A (string) directory to launch in
        :param job_parameters: a JobParameters() instance
        '''
        # convert launch_dir to absolute path
        launch_dir = os.path.abspath(launch_dir)
        
        p = job_parameters.params
        
        outs = []
        outs.append('#!/bin/bash')
        outs.append('')

        if p.get('ncores', None):
            outs.append('#PBS -l mppwidth={}'.format(p['ncores']))
        
        if p.get('walltime', None):
            outs.append('#PBS -l walltime={}'.format(p['walltime']))
        
        if p.get('queue', None):
            outs.append('#PBS -q {}'.format(p['queue']))
        
        if p.get('account', None):
            outs.append('#PBS -A {}'.format(p['account']))
        
        if p.get('pbs_options', None):
            for k, v in p['pbs_options'].items():
                outs.append('#PBS -l {k}={v}'.format(k=k, v=v))
        
        if p.get('pbs_tags', None):
            for tag in p['pbs_tags']:
                outs.append('#PBS -{}'.format(tag))

        job_name = 'FW_job'
        if p.get('jobname', None):
            job_name = p['jobname']
        outs.append('#PBS -N {}'.format(job_name))
        outs.append('#PBS -o {}'.format(job_name + '.out'))
        outs.append('#PBS -e {}'.format(job_name + '.error'))
        
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
        return "\n".join(outs)
    
    def submit_to_queue(self, script_file, job_parameters):
        '''
        for documentation, see parent object
        '''
        
        if not os.path.exists(script_file):
            raise ValueError("Cannot find script file located at: {}".format(script_file))
        
        # initialize logger
        pbs_logger = get_fw_logger("rockets.pbs", job_parameters.logging_dir)
        
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
                    pbs_logger.info('Job submission was_successful and job_id is {}'.format(job_id))
                    return job_id
                except:
                    # probably error parsing job code
                    log_exception(pbs_logger, 'Could not parse job id following qsub...')
                    
            else:
                # some qsub error, e.g. maybe wrong queue specified, don't have permission to submit, etc...
                msgs = ['Error in job submission with PBS file {f} and cmd {c}'.format(f=script_file, c=cmd)]
                msgs.append('The error response reads: {}'.format(p.stderr.read()))
                log_fancy(pbs_logger, 'error', msgs)
        
        except:
            # random error, e.g. no qsub on machine!
            log_exception(pbs_logger, 'Running qsub caused an error...')
    
    def get_njobs_in_queue(self, job_parameters, username=None):
        '''
        for documentation, see parent object
        '''
        
        # TODO: (low-priority) parse the qstat -x output as an alternate way to get this working
        # tmp_file_name = 'tmp_qstat.xml'
        # cmd = ['qstat', '-x']\n

        # initialize logger
        pbs_logger = get_fw_logger("rockets.pbs", job_parameters.logging_dir)
        
        # initialize username
        if username is None:
            username = getpass.getuser()

        # run qstat
        cmd = ['qstat', '-a', '-u', username]
        p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
        p.wait()

        # parse the result
        if p.returncode == 0:
            # lines should have this form
            # '1339044.sdb          username  queuename    2012-02-29-16-43  20460   --   --    --  00:20 C 00:09'
            # count lines that include the username in it
            
            # TODO: only count running or queued jobs. or rather, *don't* count jobs that are 'C'.
            outs = p.stdout.readlines()
            rx = re.compile(username)
            njobs = len([line.split() for line in outs if rx.search(line) is not None])
            pbs_logger.info('The number of jobs currently in the queue is: {}'.format(njobs))        
            return njobs
        
        # there's a problem talking to qstat server?
        msgs = ['Error trying to get the number of jobs in the queue using qstat service']
        msgs.append('The error response reads: {}'.format(p.stderr.read()))
        log_fancy(pbs_logger, 'error', msgs)
        return None
