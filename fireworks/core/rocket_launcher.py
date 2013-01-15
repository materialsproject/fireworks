#!/usr/bin/env python

'''
This module is used to submit jobs to a queue on a cluster. It can submit a single job, \
or if used in "rapid-fire" mode, can submit multiple jobs within a directory structure. \
The details of job submission and queue communication are handled using JobParameters, \
which specifies a QueueAdapter as well as desired properties of the submit script.
'''

import os
import glob
import datetime
import time
from fireworks.utilities.fw_utilities import get_fw_logger, log_exception
from fireworks.core.fw_constants import FW_BLOCK_FORMAT, QUEUE_UPDATE_INTERVAL, \
QUEUE_RETRY_ATTEMPTS, SUBMIT_SCRIPT_NAME

__author__ = 'Anubhav Jain, Michael Kocher'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'


def launch_rocket(job_params, launch_dir='.'):
    '''
    Submit a single job to the queue.
    
    :param job_params: A JobParameters instance
    :param launch_dir: The directory where to submit the job
    '''
    
    # convert launch_dir to absolute path
    launch_dir = os.path.abspath(launch_dir)
    
    # initialize logger
    l_logger = get_fw_logger('rockets.launcher', job_params.logging_dir)
    
    # make sure launch_dir exists:
    if not os.path.exists(launch_dir):
        raise ValueError('Desired launch directory {} does not exist!'.format(launch_dir))
    
    try:
        # get the queue adapter
        l_logger.info('getting queue adapter')
        qa = job_params.qa
        
        # move to the launch directory.
        l_logger.info('moving to launch_dir {}'.format(launch_dir))
        os.chdir(launch_dir)
        
        # write and submit the queue script using the queue adapter
        l_logger.info('writing queue script')
        with open(SUBMIT_SCRIPT_NAME, 'w') as f:
            queue_script = qa.get_script_str(job_params, launch_dir)
            if not queue_script:
                raise RuntimeError('queue script could not be written, check job params and queue adapter!')
            f.write(queue_script)
        l_logger.info('submitting queue script')
        if not qa.submit_to_queue(job_params, SUBMIT_SCRIPT_NAME):
            raise RuntimeError('queue script could not be submitted, check queue adapter and queue server status!')
    
    except:
        log_exception(l_logger, 'Error launching rocket!')


def rapid_fire(job_params, launch_dir='.', njobs_queue=10, njobs_block=500, n_loops=1, t_sleep=3600):
    '''
    Used to submit many jobs to the queue.
    
    :param job_params: A JobParameters instance
    :param launch_dir: directory where we want to write the blocks
    :param njobs_queue: stops submitting jobs when njobs_queue jobs are in the queue
    :param njobs_block: automatically write a new block when njobs_block jobs are in a single block
    :param n_loops: number of times to loop rapid-fire mode to maintain njobs_queue
    :param t_sleep: sleep time between loops in rapid-fire mode
    '''
    
    # convert launch_dir to absolute path
    launch_dir = os.path.abspath(launch_dir)
    
    # initialize logger
    l_logger = get_fw_logger('rockets.launcher', job_params.logging_dir)
    
    # make sure launch_dir exists:
    if not os.path.exists(launch_dir):
        raise ValueError('Desired launch directory {} does not exist!'.format(launch_dir))
        
    try:
        l_logger.info('getting queue adapter')
        qa = job_params.qa
        
        block_dir = _create_datestamp_dir(launch_dir, l_logger)
        
        for i in range(n_loops):
            if i > 0:
                # sleep before new loop
                l_logger.info('Sleeping for {} seconds before beginning new loop...zzz...'.format(t_sleep))
                time.sleep(t_sleep)
            
            l_logger.info('Beginning loop number {}'.format(i))
            
            # get number of jobs in queue
            jobs_in_queue = _get_number_of_jobs_in_queue(job_params, njobs_queue, l_logger)
                
            # if too few jobs, launch some more!
            while jobs_in_queue < njobs_queue:
                l_logger.info('Launching a rocket!')
                
                # switch to new block dir if it got too big
                if _njobs_in_dir(block_dir) >= njobs_block:
                    l_logger.info('Block got bigger than {} jobs.'.format(njobs_block))
                    block_dir = _create_datestamp_dir(launch_dir, l_logger)
                
                # create launcher_dir
                launcher_dir = _create_datestamp_dir(block_dir, l_logger, prefix='launcher_')
                # launch a single job
                launch_rocket(job_params, launcher_dir)
                # wait for the queue system to update
                l_logger.info('Sleeping for {} seconds...zzz...'.format(QUEUE_UPDATE_INTERVAL))
                time.sleep(QUEUE_UPDATE_INTERVAL)
                jobs_in_queue = _get_number_of_jobs_in_queue(job_params, njobs_queue, l_logger)
    
    except:
        log_exception(l_logger, 'Error with rapid fire!')


def _njobs_in_dir(block_dir):
    '''
    Internal method to count the number of jobs inside a block
    :param block_dir: the block directory we want to count the jobs in
    '''
    return len(glob.glob('%s/launcher_*' % os.path.abspath(block_dir)))


def _get_number_of_jobs_in_queue(job_params, njobs_queue, l_logger):
    '''
    Internal method to get the number of jobs in the queue using the given job params. \
    In case of failure, automatically retries at certain intervals...
    
    :param job_params: a JobParameters() instance
    :param njobs_queue: The maximum number of jobs in the queue desired
    :param l_logger: A logger to put errors/info/warnings/etc.
    '''

    RETRY_INTERVAL = 30  # initial retry in 30 sec upon failure
    
    jobs_in_queue = job_params.qa.get_njobs_in_queue(job_params)
    for i in range(QUEUE_RETRY_ATTEMPTS):
        if jobs_in_queue is not None:
            l_logger.info('{} jobs in queue. Desired: {}'.format(jobs_in_queue, njobs_queue))
            return jobs_in_queue
        l_logger.warn('Could not get number of jobs in queue! Sleeping {} secs...zzz...'.format(RETRY_INTERVAL))
        time.sleep(RETRY_INTERVAL)
        RETRY_INTERVAL = RETRY_INTERVAL * 2
        jobs_in_queue = job_params.qa.get_njobs_in_queue(job_params)
    
    raise RuntimeError('Unable to determine number of jobs in queue, check queue adapter and queue server status!')
        
    
def _create_datestamp_dir(root_dir, l_logger, prefix='block_'):
    '''
    Internal method to create a new block or launcher directory. \
    The dir name is based on the time and the FW_BLOCK_FORMAT
    :param root_dir: directory to create the new dir in
    :param l_logger: the logger to use
    :param prefix: the prefix for the new dir, default="block_"
    '''
    
    time_now = datetime.datetime.utcnow().strftime(FW_BLOCK_FORMAT)
    block_path = prefix + time_now
    full_path = os.path.join(root_dir, block_path)
    os.mkdir(full_path)
    l_logger.info('Created new dir {}'.format(full_path))
    return full_path