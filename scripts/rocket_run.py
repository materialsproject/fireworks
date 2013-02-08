#!/usr/bin/env python

'''
TODO: add docs
'''
from argparse import ArgumentParser
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket import Rocket
from fireworks.core.fworker import FWorker


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
    parser.add_argument('-w', '--worker_file', help='path to worker file', default=None)
    
    args = parser.parse_args()
    
    if args.launchpad_file:
        launchpad = LaunchPad.from_file(args.launchpad_file)
    else:
        launchpad = LaunchPad()
    
    if args.worker_file:
        fworker = FWorker.from_file(args.launchpad_file)
    else:
        fworker = FWorker()
    
    rocket = Rocket(launchpad, fworker)
    rocket.run()