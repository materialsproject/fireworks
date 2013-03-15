#!/usr/bin/env python

"""
A set of global constants for FireWorks (Python code as a config file)
"""


import logging
import datetime
import os
import yaml

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

YAML_STYLE = False  # controls whether YAML documents will be nested as braces or blocks (False = blocks)
USER_PACKAGES = ['fireworks.user_objects', 'fireworks.utilities.tests',
                 'fw_tutorials']  # this is where load_object() looks for serialized objects

FW_NAME_UPDATES = {}  # if you update a _fw_name, you can use this to record the change and maintain deserialization 
FW_BLOCK_FORMAT = '%Y-%m-%d-%H-%M-%S-%f'  # date format for writing block directories in "rapid-fire" mode
FW_LOGGING_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(message)s')  # format for loggers

QUEUE_RETRY_ATTEMPTS = 10  # number of attempts to re-try communicating with queue server in certain cases
QUEUE_UPDATE_INTERVAL = 15  # max interval (seconds) needed for queue to update after submitting a job

SUBMIT_SCRIPT_NAME = 'FW_submit.script'  # name of submit script

DATETIME_HANDLER = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None

PRINT_FW_JSON = True
PRINT_FW_YAML = False

PING_TIME_SECS = 3600  # while Running a job, how often to ping back the server that we're still alive

RESERVATION_EXPIRATION_SECS = 60 * 60 * 24 * 14  # a job can stay in a queue for 14 days before we cancel its reservation
RUN_EXPIRATION_SECS = PING_TIME_SECS * 4  # if a job is not pinged in this much time, we mark it FIZZLED

from fireworks.utilities.fw_utilities import singleton


@singleton
class FWConfig(object):
    def __init__(self):

        self.USER_PACKAGES = ['fireworks.user_objects', 'fireworks.utilities.tests',
                              'fw_tutorials']  # this is where load_object() looks for serialized objects

        self.apply_user_settings()

    def apply_user_settings(self):
        root_dir = os.path.dirname(os.path.dirname(MODULE_DIR))
        config_path = os.path.join(root_dir, 'fw_config.yaml')

        if os.path.exists(config_path):
            with open(config_path) as f:
                overrides = yaml.load(f.read())
                for key, v in overrides.iteritems():
                    self.__setattr__(key, v)