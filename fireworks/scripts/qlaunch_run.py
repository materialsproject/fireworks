#!/usr/bin/env python

"""
A runnable script for launching rockets (a command-line interface to queue_launcher.py)
"""

from argparse import ArgumentParser
import os
from fireworks.core.fw_config import FWConfig
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad
from fireworks.queue.queue_launcher import rapidfire, launch_rocket_to_queue
from fireworks.utilities.fw_serializers import load_object_from_file

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 14, 2013"


def qlaunch():
    m_description = 'This program is used to submit jobs to a queueing system. Details of the job and queue \
    interaction are handled by the mandatory queue adapter file parameter. The "rapidfire" option can be used \
    to maintain a certain number of jobs in the queue by specifying the n_loops parameter to a large number. \
    If n_loops is set to 1 (default) the queue launcher will quit after submitting the desired number of jobs. \
    For more help on rapid fire options, use qlauncher.py rapidfire -h'

    parser = ArgumentParser(description=m_description)
    subparsers = parser.add_subparsers(help='command', dest='command')
    single_parser = subparsers.add_parser('singleshot', help='launch a single rocket to the queue')
    rapid_parser = subparsers.add_parser('rapidfire', help='launch multiple rockets to the queue')

    parser.add_argument('--launch_dir', help='directory to launch the job / rapid-fire', default='.')
    parser.add_argument('--logdir', help='path to a directory for logging', default=None)
    parser.add_argument('--loglvl', help='level to print log messages', default='INFO')
    parser.add_argument('-s', '--silencer', help='shortcut to mute log messages', action='store_true')
    parser.add_argument('-r', '--reserve', help='reserve a fw', action='store_true')
    parser.add_argument('-l', '--launchpad_file', help='path to launchpad file', default=FWConfig().LAUNCHPAD_LOC)
    parser.add_argument('-w', '--fworker_file', help='path to fworker file', default=FWConfig().FWORKER_LOC)
    parser.add_argument('-q', '--queueadapter_file', help='path to queueadapter file',
                        default=FWConfig().QUEUEADAPTER_LOC)
    parser.add_argument('-c', '--config_dir',
                        help='path to a directory containing the config file (used if -l, -w, -q unspecified)',
                        default=FWConfig().CONFIG_FILE_DIR)

    rapid_parser.add_argument('-m', '--maxjobs_queue', help='maximum jobs to keep in queue for this user', default=10,
                              type=int)
    rapid_parser.add_argument('-b', '--maxjobs_block', help='maximum jobs to put in a block', default=500, type=int)
    rapid_parser.add_argument('--nlaunches', help='num_launches (int or "infinite"; default 0 is all jobs in DB)', default=0)
    rapid_parser.add_argument('--sleep', help='sleep time between loops', default=None, type=int)

    args = parser.parse_args()

    if not args.launchpad_file and os.path.exists(os.path.join(args.config_dir, 'my_launchpad.yaml')):
        args.launchpad_file = os.path.join(args.config_dir, 'my_launchpad.yaml')

    if not args.fworker_file and os.path.exists(os.path.join(args.config_dir, 'my_fworker.yaml')):
        args.fworker_file = os.path.join(args.config_dir, 'my_fworker.yaml')

    if not args.queueadapter_file and os.path.exists(os.path.join(args.config_dir, 'my_qadapter.yaml')):
        args.queueadapter_file = os.path.join(args.config_dir, 'my_qadapter.yaml')

    launchpad = LaunchPad.from_file(args.launchpad_file) if args.launchpad_file else LaunchPad(strm_lvl=args.loglvl)
    fworker = FWorker.from_file(args.fworker_file) if args.fworker_file else FWorker()
    queueadapter = load_object_from_file(args.queueadapter_file)
    args.loglvl = 'CRITICAL' if args.silencer else args.loglvl

    if args.command == 'rapidfire':
        rapidfire(launchpad, fworker, queueadapter, args.launch_dir, args.nlaunches, args.maxjobs_queue,
                  args.maxjobs_block, args.sleep, args.reserve, args.loglvl)
    else:
        launch_rocket_to_queue(launchpad, fworker, queueadapter, args.launch_dir, args.reserve, args.loglvl)


if __name__ == '__main__':
    qlaunch()