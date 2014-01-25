#!/usr/bin/env python

"""
A set of global constants for FireWorks (Python code as a config file)
"""

import os
import yaml

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'


NEGATIVE_FWID_CTR = 0

def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
class FWConfig(object):
    def __init__(self):

        self.USER_PACKAGES = ['fireworks.user_objects', 'fireworks.utilities.tests',
                              'fw_tutorials']  # this is where load_object() looks for serialized objects

        self.FW_NAME_UPDATES = {'Transfer Task': 'FileTransferTask', 'Script Task': 'ScriptTask', 'Template Writer Task':'TemplateWriterTask', 'Dupe Finder Exact': 'DupeFinderExact'}  # if you update a _fw_name, you can use this to record the change and maintain
        # deserialization

        self.YAML_STYLE = False  # controls whether YAML documents will be nested as braces or blocks (False = blocks)

        self.FW_BLOCK_FORMAT = '%Y-%m-%d-%H-%M-%S-%f'  # date format for writing block directories in "rapid-fire" mode

        self.FW_LOGGING_FORMAT = '%(asctime)s %(levelname)s %(message)s'  # format for loggers

        self.QUEUE_RETRY_ATTEMPTS = 10  # number of attempts to re-try communicating with queue server in failures
        self.QUEUE_UPDATE_INTERVAL = 15  # max interval (seconds) needed for queue to update after submitting a job

        self.SUBMIT_SCRIPT_NAME = 'FW_submit.script'  # name of submit script

        self.PRINT_FW_JSON = True
        self.PRINT_FW_YAML = False

        self.PING_TIME_SECS = 3600  # while Running a job, how often to ping back the server that we're still alive
        self.RUN_EXPIRATION_SECS = self.PING_TIME_SECS * 4  # mark job as FIZZLED if not pinged in this time

        self.MAINTAIN_INTERVAL = 120  # seconds between maintenance intervals when running infinite maintenance

        self.RESERVATION_EXPIRATION_SECS = 60 * 60 * 24 * 14  # a job can stay in a queue this long before we
        # cancel its reservation

        self.RAPIDFIRE_SLEEP_SECS = 60  # seconds to sleep between rapidfire loops

        self.LAUNCHPAD_LOC = None  # where to find the my_launchpad.yaml file
        self.FWORKER_LOC = None  # where to find the my_fworker.yaml file
        self.QUEUEADAPTER_LOC = None  # where to find the my_queueadapter.yaml file

        self.CONFIG_FILE_DIR = '.'  # directory containing config files (if not individually set)

        self.QSTAT_FREQUENCY = 50  # set this higher to avoid qstats, lower to alwas

        self.ALWAYS_CREATE_NEW_BLOCK = False  # always create new block on queue launcher call

        self.TEMPLATE_DIR = None  # default template dir for TemplateWriterTask

        self.REMOVE_USELESS_DIRS = True  # deletes empty launch dir if _launch_dir set

        self.DS_PASSWORD = '1234'  # dummy password to access DataServer

        self.STORE_PACKING_INFO = True  # automatically add job packing info to stored_data

        self.PW_CHECK_NUM = 10  # number of entries that can be modified in single lpad command w/o password

        self.TRACKER_LINES = 25  # number of lines to return in Tracker

        self.SORT_FWS = ''  # sort equal priority FWs? "FILO" or "FIFO".

        self.override_user_settings()

    def override_user_settings(self):

        MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(MODULE_DIR))  # FW root dir

        if os.path.exists(os.path.join(os.getcwd(), 'FW_config.yaml')):
            config_path=os.path.join(os.getcwd(), 'FW_config.yaml')

        elif "FW_CONFIG_FILE" in os.environ:
            config_path = os.environ['FW_CONFIG_FILE']

        elif os.path.exists(os.path.join(root_dir, 'FW_config.yaml')):
            config_path=os.path.join(root_dir, 'FW_config.yaml')

        else:
            config_path = os.path.join(os.environ["HOME"], ".fireworks",
                                       'FW_config.yaml')

        if os.path.exists(config_path):
            with open(config_path) as f:
                overrides = yaml.load(f.read())
                for key, v in overrides.iteritems():
                    if key == 'ADD_USER_PACKAGES':
                        self.USER_PACKAGES.extend(v)
                    elif key == 'ECHO_TEST':
                        print v
                    elif not hasattr(self, key):
                        raise ValueError(
                            'Invalid FW_config file has unknown parameter: {}'.format(
                                key))
                    else:
                        self.__setattr__(key, v)

        for k in ["LAUNCHPAD_LOC", "FWORKER_LOC", "QUEUEADAPTER_LOC"]:
            fname = "my_{}.yaml".format(k.split("_")[0].lower())
            default_path = os.path.join(
                    os.environ["HOME"], ".fireworks", fname)
            if getattr(self, k, None) is None and os.path.exists(default_path):
                self.__setattr__(k, default_path)

    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            d[k] = v
        return d

    def write_config(self, path=None):
        path = os.path.join(os.environ["HOME"], ".fireworks",
                            'FW_config.yaml') if path is None else path
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f)


@singleton
class FWData(object):
    """
    This class stores data that a FireTask might want to access, e.g. to see the runtime params
    """

    def __init__(self):
        self.MULTIPROCESSING = None # default single process framework
        self.NODE_LIST = None  # the node list for sub jobs
        self.SUB_NPROCS = None  # the number of process of the sub job
        self.DATASERVER = None  # the shared object manager