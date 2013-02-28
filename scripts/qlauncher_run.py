#!/usr/bin/env python

"""
A runnable script for launching rockets (a command-line interface to queue_launcher.py)
"""

from argparse import ArgumentParser
from fireworks.core.launchpad import LaunchPad
from fireworks.core.queue_launcher import rapidfire, launch_rocket_to_queue
from fireworks.core.fworker import QueueParams

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 14, 2013"


if __name__ == '__main__':
    m_description = 'This program is used to submit jobs to a queueing system. Details of the job and queue \
    interaction are handled by the mandatory queue params file parameter. The "rapidfire" option can be used \
    to maintain a certain number of jobs in the queue by specifying the n_loops parameter to a large number. \
    If n_loops is set to 1 (default) the queue launcher will quit after submitting the desired number of jobs. \
    For more help on rapid fire options, use qlauncher.py rapidfire -h'
    
    parser = ArgumentParser(description=m_description)
    subparsers = parser.add_subparsers(help='command', dest='command')
    single_parser = subparsers.add_parser('singleshot', help='launch a single rocket to the queue')
    rapid_parser = subparsers.add_parser('rapidfire', help='launch multiple rockets to the queue')
    
    parser.add_argument('queue_params_file', help='path to a file containing the queue parameters')
    parser.add_argument('--launch_dir', help='directory to launch the job / rapid-fire', default='.')
    parser.add_argument('--logdir', help='path to a directory for logging', default=None)
    parser.add_argument('--loglvl', help='level to print log messages', default='INFO')
    parser.add_argument('--silencer', help='shortcut to mute log messages', action='store_true')
    
    rapid_parser.add_argument('-q', '--njobs_queue', help='maximum jobs to keep in queue for this user', default=10, type=int)
    rapid_parser.add_argument('-b', '--njobs_block', help='maximum jobs to put in a block', default=500, type=int)
    rapid_parser.add_argument('--infinite', help='loop forever', action='store_true')
    rapid_parser.add_argument('--sleep', help='sleep time between loops', default=60, type=int)
    rapid_parser.add_argument('-l', '--launchpad_file', help='path to launchpad file', default=None)
    
    args = parser.parse_args()
    
    rocket_params = QueueParams.from_file(args.queue_params_file)
    args.loglvl = 'CRITICAL' if args.silencer else args.loglvl

    if args.command == 'rapidfire':
        launchpad = LaunchPad.from_file(args.launchpad_file) if args.launchpad_file else None
        rapidfire(rocket_params, args.launch_dir, args.njobs_queue, args.njobs_block, args.logdir, args.loglvl, args.infinite, args.t_sleep, launchpad)
    else:
        launch_rocket_to_queue(rocket_params, args.launch_dir, args.logdir, args.loglvl)
