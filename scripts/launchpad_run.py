#!/usr/bin/env python

'''
A runnable script for managing a FireWorks database (a command-line interface to launchpad.py)
'''
from argparse import ArgumentParser
from fireworks.core.launchpad import LaunchPad
from fireworks.core.firework import FireWork


__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'

if __name__ == '__main__':
    m_description = 'This script is used for creating and managing a FireWorks database. For a list \
    of available commands, type "launchpad_run.py -h". For more help on a specific command, type \
    "launchpad_run.py <command> -h".'
    
    parser = ArgumentParser(description=m_description)
    subparsers = parser.add_subparsers(help='command', dest='command')
    initialize_parser = subparsers.add_parser('initialize', help='initialize a FireWorks database')
    upsert_parser = subparsers.add_parser('upsert_fw', help='insert or update a FireWork from file')
    
    parser.add_argument('launchpad_file', help='path to a LaunchPad file')
    
    initialize_parser.add_argument('password', help="Today's date, e.g. 2012-02-25. Required to prevent \
    against accidental initializations.")
    
    upsert_parser.add_argument('fw_file', help="path to a FireWorks file")
    
    args = parser.parse_args()
    
    lp = LaunchPad.from_file(args.launchpad_file)
    
    if args.command == 'initialize':
        lp.initialize(args.password)
    
    if args.command == 'upsert_fw':
        fw = FireWork.from_file(args.fw_file)
        lp.upsert_fw(fw)

