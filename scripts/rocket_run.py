#!/usr/bin/env python

"""
A runnable script to launch a single Rocket (a command-line interface to rocket.py)
"""
from argparse import ArgumentParser
import os
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket import Rocket, loop_rocket_run
from fireworks.core.fworker import FWorker
from fireworks.utilities.fw_utilities import create_datestamp_dir, get_fw_logger


__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'

if __name__ == '__main__':
    m_description = 'Grabs a job from the db and runs it'
    
    parser = ArgumentParser(description=m_description)
    
    parser.add_argument('-l', '--launchpad_file', help='path to launchpad file', default=None)
    parser.add_argument('-w', '--fworker_file', help='path to fworker file', default=None)
    parser.add_argument('--loop', help='loop until error', action='store_true')

    args = parser.parse_args()
    
    if args.launchpad_file:
        launchpad = LaunchPad.from_file(args.launchpad_file)
    else:
        launchpad = LaunchPad()
    
    if args.fworker_file:
        fworker = FWorker.from_file(args.fworker_file)
    else:
        fworker = FWorker()

    if args.loop:
        loop_rocket_run(launchpad, fworker)

    else:
        rocket = Rocket(launchpad, fworker)
        rocket.run()