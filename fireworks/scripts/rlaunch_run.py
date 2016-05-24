# coding: utf-8

from __future__ import unicode_literals

"""
A runnable script to launch a single Rocket (a command-line interface to rocket_launcher.py)
"""
from argparse import ArgumentParser
import os
import signal
import sys
from fireworks.fw_config import LAUNCHPAD_LOC, FWORKER_LOC, CONFIG_FILE_DIR
from fireworks.core.launchpad import LaunchPad
from fireworks.core.fworker import FWorker
from fireworks.core.rocket_launcher import rapidfire, launch_rocket
from fireworks.utilities.fw_utilities import get_my_host, get_my_ip, get_fw_logger

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'


def handle_interrupt(signum, frame):
    sys.stderr.write("Interruped by signal {:d}\n".format(signum))
    sys.exit(1)


def rlaunch():

    m_description = 'This program launches one or more Rockets. A Rocket grabs a job from the central database and ' \
                    'runs it. The "single-shot" option launches a single Rocket, ' \
                    'whereas the "rapidfire" option loops until all FireWorks are completed.'

    parser = ArgumentParser(description=m_description)
    subparsers = parser.add_subparsers(help='command', dest='command')
    single_parser = subparsers.add_parser('singleshot', help='launch a single Rocket')
    rapid_parser = subparsers.add_parser('rapidfire',
                                         help='launch multiple Rockets (loop until all FireWorks complete)')

    single_parser.add_argument('-f', '--fw_id', help='specific fw_id to run', default=None, type=int)
    single_parser.add_argument('--offline', help='run in offline mode (FW.json required)', action='store_true')

    rapid_parser.add_argument('--nlaunches', help='num_launches (int or "infinite"; default 0 is all jobs in DB)', default=0)
    rapid_parser.add_argument('--timeout', help='timeout (secs) after which to quit (default None)', default=None, type=int)
    rapid_parser.add_argument('--max_loops', help='after this many sleep loops, quit even in infinite nlaunches mode (default -1 is infinite loops)', default=-1, type=int)
    rapid_parser.add_argument('--sleep', help='sleep time between loops (secs)', default=None, type=int)

    parser.add_argument('-l', '--launchpad_file', help='path to launchpad file', default=LAUNCHPAD_LOC)
    parser.add_argument('-w', '--fworker_file', help='path to fworker file', default=FWORKER_LOC)
    parser.add_argument('-c', '--config_dir', help='path to a directory containing the config file (used if -l, -w unspecified)',
                        default=CONFIG_FILE_DIR)

    parser.add_argument('--loglvl', help='level to print log messages', default='INFO')
    parser.add_argument('-s', '--silencer', help='shortcut to mute log messages', action='store_true')

    args = parser.parse_args()

    signal.signal(signal.SIGINT, handle_interrupt)  # graceful exit on ^C

    if not args.launchpad_file and os.path.exists(os.path.join(args.config_dir, 'my_launchpad.yaml')):
        args.launchpad_file = os.path.join(args.config_dir, 'my_launchpad.yaml')

    if not args.fworker_file and os.path.exists(os.path.join(args.config_dir, 'my_fworker.yaml')):
        args.fworker_file = os.path.join(args.config_dir, 'my_fworker.yaml')

    args.loglvl = 'CRITICAL' if args.silencer else args.loglvl

    if args.command == 'singleshot' and args.offline:
        launchpad = None
    else:
        launchpad = LaunchPad.from_file(args.launchpad_file) if args.launchpad_file else LaunchPad(strm_lvl=args.loglvl)

    if args.fworker_file:
        fworker = FWorker.from_file(args.fworker_file)
    else:
        fworker = FWorker()

    # prime addr lookups
    _log = get_fw_logger("rlaunch", stream_level="INFO")
    _log.info("Hostname/IP lookup (this will take a few seconds)")
    get_my_host()
    get_my_ip()

    if args.command == 'rapidfire':
        rapidfire(launchpad, fworker=fworker, m_dir=None, nlaunches=args.nlaunches,
                  max_loops=args.max_loops, sleep_time=args.sleep, strm_lvl=args.loglvl,
                  timeout=args.timeout)

    else:
        launch_rocket(launchpad, fworker, args.fw_id, args.loglvl)

if __name__ == '__main__':
    rlaunch()
