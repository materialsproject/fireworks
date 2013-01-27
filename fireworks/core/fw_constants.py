#!/usr/bin/env python

'''
A set of global constants for FireWorks (Python code as a config file)
'''

import logging

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'

YAML_STYLE = False  # controls whether YAML documents will be nested as braces or blocks (False = blocks)
USER_PACKAGES = ['fireworks.utilities.tests', 'fireworks.user_objects']  # this is where load_object() looks for serialized objects

FW_NAME_UPDATES = {}  # if you update a _fw_name, you can use this to record the change and maintain deserialization 
FW_BLOCK_FORMAT = '%Y-%m-%d-%H-%M-%S-%f'  # date format for writing block directories in "rapid-fire" mode
FW_LOGGING_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(message)s')  # format for loggers

QUEUE_RETRY_ATTEMPTS = 10  # number of attempts to re-try communicating with queue server in certain cases
QUEUE_UPDATE_INTERVAL = 30  # max interval (seconds) needed for queue to update after submitting a job

SUBMIT_SCRIPT_NAME = 'submit.script'  # name of submit script