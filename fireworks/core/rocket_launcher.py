#!/usr/bin/env python

'''
This module is used to submit jobs to a queue on a cluster. It can submit a single job, \
or if used in "rapid-fire" mode, can submit multiple jobs within a directory structure.

The details of job submission and queue communication are handled using JobParameters.

You can directly run this module from the command line on your cluster. See docs of \
the __main__ method for details.
'''

import os
import glob
import datetime
import time
from fireworks.core.queue_adapter_base import JobParameters
from argparse import ArgumentParser
from fireworks.utilities.fw_utilities import get_fw_logger,\
    log_exception
from fireworks.core.fw_constants import FW_BLOCK_FORMAT,\
    QUEUE_UPDATE_INTERVAL, QUEUE_RETRY_ATTEMPTS

__author__ = 'Anubhav Jain, Michael Kocher'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'


def launch_rocket(job_params, launch_dir='.', script_filename='submit.script'):
    '''
    Submit a single job to the queue.
    
    :param job_params: A JobParameters instance
    :param launch_dir: The directory where to submit the job
    :param script_filename: desired name for script file
    '''
    
    # initialize logger
    l_logger = get_fw_logger('rockets.launcher', job_params.logging_dir)
    
    try:
        # get the queue adapter
        l_logger.info('getting queue adapter')
        qa = job_params.qa
        
        # write the script file in the launch dir
        script_filename = os.path.join(launch_dir, script_filename)
        
        # write and submit the queue script using the queue adapter
        l_logger.info('writing queue script in location {}'.format(script_filename))
        with open(script_filename, 'w') as f:
            queue_script = qa.get_script_str(launch_dir, job_params)
            if not queue_script:
                raise RuntimeError('queue script could not be written, check job params and queue adapter!')
            f.write(queue_script)
            l_logger.info('submitting queue script, {}'.format(script_filename))
            if not qa.submit_to_queue(script_filename, job_params):
                raise RuntimeError('queue script could not be submitted, check queue adapter and queue server status!')
    
    except:
        log_exception(l_logger, 'Error launching rocket!')


def rapid_fire(job_params, launch_dir='.', script_filename='submit.script', njobs_queue=10, njobs_block=500, n_loops=1, t_sleep=3600):
    '''
    Used to submit many jobs to the queue.
    
    :param job_params: A JobParameters instance
    :param launch_dir: directory where we want to write the blocks
    :param script_filename: desired name for script file
    :param njobs_queue: stops submitting jobs when njobs_queue jobs are in the queue
    :param njobs_block: automatically write a new block when njobs_block jobs are in a single block
    :param n_loops: number of times to loop rapid-fire mode to maintain njobs_queue
    :param t_sleep: sleep time between loops in rapid-fire mode
    '''
    
    # initialize logger
    l_logger = get_fw_logger('rockets.launcher', job_params.logging_dir)
    
    try:
        l_logger.info('getting queue adapter')
        qa = job_params.qa
        
        block_dir = _create_datestamp_dir(launch_dir, l_logger)
        
        for i in range(n_loops):
            l_logger.info('Beginning loop number {}'.format(i))
            
            # switch to new block dir if it got too big
            if _njobs_in_dir(block_dir) >= njobs_block:
                l_logger.info('Block got bigger than {} jobs.'.format(njobs_block))
                block_dir = _create_datestamp_dir(launch_dir, l_logger)
            
            # get number of jobs in queue
            jobs_in_queue = _get_number_of_jobs_in_queue(job_params, njobs_queue, l_logger)
                
            # if too few jobs, launch some more!
            while jobs_in_queue < njobs_queue:
                l_logger.info('Launching a rocket!')
                # create launcher_dir
                launcher_dir = _create_datestamp_dir(block_dir, l_logger, prefix='launcher_')
                # launch a single job
                launch_rocket(job_params, launcher_dir, script_filename)
                # wait for the queue system to update
                time.sleep(QUEUE_UPDATE_INTERVAL)
                jobs_in_queue = _get_number_of_jobs_in_queue(job_params, qa, l_logger)
    
            l_logger.info('Loop finished, sleeping for {} seconds...').format(t_sleep)
            time.sleep(t_sleep)
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
        l_logger.warn('Could not get number of jobs in queue! Sleeping {} secs...'.format(RETRY_INTERVAL))
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
    l_logger.info('Created new block {}'.format(full_path))
    return full_path
    
#TODO: make rocket launcher a script in the distutils distribution so it is more easily run
    
if __name__ == '__main__':
    m_description = 'This program is used to submit jobs to a queueing system. Details of the job \
    and queue system interaction are handled by the specified job parameters file. By default, a \
    single job is submitted. To submit many jobs, use the "rapid-fire" option. The "rapid-fire" \
    option can also be used to maintain a certain number of jobs in the queue by specifying the \
    n_loops parameter to a large number. If n_loops is set to 1 (default) we will quit after \
    submitting the desired number of jobs.'
    
    parser = ArgumentParser(description=m_description)
    parser.add_argument('job_params', help='The location of a file containing the job parameters (JobParams serialization)')
    parser.add_argument('-l', '--launch_dir', help='directory to launch the job / rapid-fire', default='.')
    parser.add_argument('-s', '--script_filename', help='name of script file', default='submit.script')
    parser.add_argument('--rapidfire', help='use rapid-fire mode (launch multiple jobs)', action='store_false')
    parser.add_argument('-q', '--njobs_queue', help='maximum jobs to keep in queue for this user (rapid-fire mode only)', default=10)
    parser.add_argument('-b', '--njobs_block', help='maximum jobs to put in a block (rapid-fire mode only)', default=500)
    parser.add_argument('-n', '--n_loops', help='number of times to loop to maintain njobs_queue (rapid-fire mode only)', default=1)
    parser.add_argument('-t', '--t_sleep', help='sleep time (seconds) between loops (rapid-fire mode only)', default=3600)
    args = parser.parse_args()
    job_params = JobParameters.from_file(args.job_params)
    if args.rapidfire:
        rapid_fire(job_params, args.launch_dir, args.script_filename, args.njobs_queue, args.njobs_block, args.n_loops, args.t_sleep)
    else:
        launch_rocket(job_params, args.launch_dir, args.script_filename)