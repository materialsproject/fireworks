#!/usr/bin/env python

'''
A runnable script for managing a FireWorks database (a command-line interface to launchpad.py)
'''
from argparse import ArgumentParser
from fireworks.core.launchpad import FWDatabase, LaunchPad


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
    
    parser.add_argument('fw_db_file', help='path to a FWDatabase file')
    
    initialize_parser.add_argument('password', help="Today's date, e.g. 2012-02-25. Required to prevent \
    against accidental initializations.")
    
    args = parser.parse_args()
    
    fw_db = FWDatabase.from_file(args.fw_db_file)
    lp = LaunchPad(fw_db)
    
    if args.command == 'initialize':
        lp.initialize(args.password)

