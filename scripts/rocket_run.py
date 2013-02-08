#!/usr/bin/env python

'''
TODO: add docs
'''
from argparse import ArgumentParser
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket import Rocket


__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'

if __name__ == '__main__':
    m_description = 'Grabs a job from the db and runs it'
    
    parser = ArgumentParser(description=m_description)
    
    parser.add_argument('-l', '--launchpad_file', help='path to launchpad file', default='launchpad.yaml')
    
    args = parser.parse_args()
    
    launchpad = LaunchPad.from_file(args.launchpad_file)
    
    rocket = Rocket(launchpad)
    rocket.run()
