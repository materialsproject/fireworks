#!/usr/bin/env python

"""
A runnable script to launch a single Rocket (a command-line interface to rocket.py)
"""
from argparse import ArgumentParser
from fireworks.core.launchpad import LaunchPad
from fireworks.core.fworker import FWorker
from fireworks.core.rocket_launcher import loop_rocket_run, launch_rocket


__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'

if __name__ == '__main__':
    m_description = 'This program launches one or more Rockets. A Rocket grabs a job from the central database and ' \
                    'runs it. The "single-shot" option launches a single Rocket, ' \
                    'whereas the "rapid-fire" option loops until all FireWorks are completed.'

    parser = ArgumentParser(description=m_description)
    subparsers = parser.add_subparsers(help='command', dest='command')
    single_parser = subparsers.add_parser('singleshot', help='launch a single Rocket')
    rapid_parser = subparsers.add_parser('rapidfire',
                                         help='launch multiple Rockets (loop until all FireWorks complete)')

    parser.add_argument('-l', '--launchpad_file', help='path to launchpad file', default=None)
    parser.add_argument('-w', '--fworker_file', help='path to fworker file', default=None)

    args = parser.parse_args()

    if args.launchpad_file:
        launchpad = LaunchPad.from_file(args.launchpad_file)
    else:
        launchpad = LaunchPad()

    if args.fworker_file:
        fworker = FWorker.from_file(args.fworker_file)
    else:
        fworker = FWorker()

    if args.command == 'rapidfire':
        loop_rocket_run(launchpad, fworker)

    else:
        launch_rocket(launchpad, fworker)