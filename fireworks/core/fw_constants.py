#!/usr/bin/env python

"""
A set of global constants for FireWorks (Python code as a config file)
"""

import logging
import datetime

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'

YAML_STYLE = False  # controls whether YAML documents will be nested as braces or blocks (False = blocks)
USER_PACKAGES = ['fireworks.user_objects', 'fireworks.utilities.tests',
                 'fw_tutorials']  # this is where load_object() looks for serialized objects

FW_NAME_UPDATES = {}  # if you update a _fw_name, you can use this to record the change and maintain deserialization 
FW_BLOCK_FORMAT = '%Y-%m-%d-%H-%M-%S-%f'  # date format for writing block directories in "rapid-fire" mode
FW_LOGGING_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(message)s')  # format for loggers

QUEUE_RETRY_ATTEMPTS = 10  # number of attempts to re-try communicating with queue server in certain cases
QUEUE_UPDATE_INTERVAL = 15  # max interval (seconds) needed for queue to update after submitting a job

SUBMIT_SCRIPT_NAME = 'FW_submit.script'  # name of submit script

# 'Canceled' is the dominant spelling over 'cancelled' in the US starting around 1985...(Google n-grams)
LAUNCH_RANKS = {'DEFUSED': 0, 'WAITING': 1, 'READY': 2, 'FIZZLED': 3, 'RESERVED': 4, 'RUNNING': 5, 'CANCELED': 6, 'COMPLETED': 7}

DATETIME_HANDLER = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None

PRINT_FW_JSON = True