#!/usr/bin/env python

'''
TODO: add docs
'''

from argparse import ArgumentParser
from fireworks.core.queue_adapter_base import JobParameters
from fireworks.core.rocket_launcher import rapid_fire, launch_rocket

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 14, 2013"

if __name__ == '__main__':
    m_description = 'This program is used to submit jobs to a queueing system. Details of the job \
    and queue system interaction are handled by the specified job parameters file. By default, a \
    single job is submitted. To submit many jobs, use the "rapid-fire" option. The "rapid-fire" \
    option can also be used to maintain a certain number of jobs in the queue by specifying the \
    n_loops parameter to a large number. If n_loops is set to 1 (default) the rocket launcher will \
    quit after submitting the desired number of jobs.'
    
    parser = ArgumentParser(description=m_description)
    parser.add_argument('job_params', help='The location of a file containing the job parameters (JobParams serialization)')
    parser.add_argument('-l', '--launch_dir', help='directory to launch the job / rapid-fire', default='.')
    # parser.add_argument('-s', '--SUBMIT_SCRIPT_NAME', help='name of script file', default='submit.script')
    parser.add_argument('--rapidfire', help='use rapid-fire mode (launch multiple jobs)', action='store_true')
    parser.add_argument('-q', '--njobs_queue', help='maximum jobs to keep in queue for this user (rapid-fire mode only)', default=10, type=int)
    parser.add_argument('-b', '--njobs_block', help='maximum jobs to put in a block (rapid-fire mode only)', default=500, type=int)
    parser.add_argument('-n', '--n_loops', help='number of times to loop to maintain njobs_queue (rapid-fire mode only)', default=1, type=int)
    parser.add_argument('-t', '--t_sleep', help='sleep time (seconds) between loops (rapid-fire mode only)', default=3600, type=int)
    args = parser.parse_args()
    job_params = JobParameters.from_file(args.job_params)

    if args.rapidfire:
        rapid_fire(job_params, args.launch_dir, args.njobs_queue, args.njobs_block, args.n_loops, args.t_sleep)
    else:
        launch_rocket(job_params, args.launch_dir)