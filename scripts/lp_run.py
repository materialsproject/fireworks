#!/usr/bin/env python

"""
A runnable script for managing a FireWorks database (a command-line interface to launchpad.py)
"""
from argparse import ArgumentParser
from fireworks.core.fw_constants import DATETIME_HANDLER
from fireworks.core.launchpad import LaunchPad
from fireworks.core.firework import FireWork, FWorkflow
import ast
import simplejson as json

#TODO: YAML queries give weird unicode string, maybe this is unfixable though

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'

if __name__ == '__main__':
    m_description = 'This script is used for creating and managing a FireWorks database. For a list \
    of available commands, type "lp_run.py -h". For more help on a specific command, type \
    "lp_run.py <command> -h".'
    
    parser = ArgumentParser(description=m_description)
    subparsers = parser.add_subparsers(help='command', dest='command')
    
    reset_parser = subparsers.add_parser('reset', help='reset a FireWorks database')
    reset_parser.add_argument('password', help="Today's date, e.g. 2012-02-25. Required to prevent \
    against accidental initializations.")
    
    upsert_parser = subparsers.add_parser('add_fw', help='insert a single FireWork from file')
    upsert_parser.add_argument('fw_file', help="path to a FireWorks file")

    upsert_parser = subparsers.add_parser('add_wf', help='insert a FWorkflow from file')
    upsert_parser.add_argument('wf_file', help="path to a FWorkflow file")

    get_fw_parser = subparsers.add_parser('get_fw', help='get a FireWork by id')
    get_fw_parser.add_argument('fw_id', help="FireWork id", type=int)
    get_fw_parser.add_argument('-f', '--filename', help='output filename', default=None)
    
    get_fw_ids_parser = subparsers.add_parser('get_fw_ids', help='get FireWork ids by query')
    get_fw_ids_parser.add_argument('-q', '--query', help='query (as pymongo string, enclose in single-quotes)', default=None)
    
    parser.add_argument('-l', '--launchpad_file', help='path to LaunchPad file containing central DB connection info', default=None)
    
    args = parser.parse_args()
    
    if args.launchpad_file:
        lp = LaunchPad.from_file(args.launchpad_file)
    else:
        lp = LaunchPad()
    
    if args.command == 'reset':
        lp.reset(args.password)
    
    elif args.command == 'add_fw':
        fwf = FWorkflow.from_FireWork(FireWork.from_file(args.fw_file))
        lp.add_wf(fwf)

    elif args.command == 'add_wf':
        # TODO: make this cleaner
        if '.tar' in args.wf_file:
            fwf = FWorkflow.from_tarfile(args.wf_file)
        else:
            fwf = FWorkflow.from_file(args.wf_file)
        lp.add_wf(fwf)
        
    elif args.command == 'get_fw':
        fw = lp.get_fw_by_id(args.fw_id)
        fw_dict = fw.to_db_dict()
        if args.filename:
            fw.to_file(args.filename)
        else:
            print json.dumps(fw_dict, default=DATETIME_HANDLER, indent=4)
        
    elif args.command == 'get_fw_ids':
        if args.query:
            args.query = ast.literal_eval(args.query)
        print lp.get_fw_ids(args.query)
