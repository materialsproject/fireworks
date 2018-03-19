# coding: utf-8

from __future__ import unicode_literals

"""
A set of global constants for FireWorks (Python code as a config file).
"""

import os
from monty.serialization import loadfn, dumpfn
from monty.design_patterns import singleton

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'

NEGATIVE_FWID_CTR = 0

# this is where load_object() looks for serialized objects
USER_PACKAGES = ['fireworks.user_objects', 'fireworks.utilities.tests',
                 'fw_tutorials', 'fireworks.features']

# if you update a _fw_name, you can use this to record the change and maintain deserialization
FW_NAME_UPDATES = {'Transfer Task': 'FileTransferTask',
                   'Script Task': 'ScriptTask',
                   'Template Writer Task': 'TemplateWriterTask',
                   'Dupe Finder Exact': 'DupeFinderExact'}

YAML_STYLE = False  # controls whether YAML documents will be nested as braces or blocks (False = blocks)

FW_BLOCK_FORMAT = '%Y-%m-%d-%H-%M-%S-%f'  # date format for writing block directories in "rapid-fire" mode

FW_LOGGING_FORMAT = '%(asctime)s %(levelname)s %(message)s'  # format for loggers

QUEUE_RETRY_ATTEMPTS = 10  # number of attempts to re-try communicating with queue server in failures
QUEUE_UPDATE_INTERVAL = 5  # max interval (seconds) needed for queue to update after submitting a job
QUEUE_JOBNAME_MAXLEN = 20  # max length of the jobname for queue systems

SUBMIT_SCRIPT_NAME = 'FW_submit.script'  # name of submit script

PRINT_FW_JSON = True
PRINT_FW_YAML = False

PING_TIME_SECS = 3600  # while Running a job, how often to ping back the server that we're still alive
RUN_EXPIRATION_SECS = PING_TIME_SECS * 4  # mark job as FIZZLED if not pinged in this time

MAINTAIN_INTERVAL = 120  # seconds between maintenance intervals when running infinite maintenance

RESERVATION_EXPIRATION_SECS = 60 * 60 * 24 * 14  # a job can stay in a queue this long before we
# cancel its reservation

WFLOCK_EXPIRATION_SECS = 60 * 5  # wait this long for a WFLock before expiring
WFLOCK_EXPIRATION_KILL = False  # kill WFLock on expiration (or give a warning)

RAPIDFIRE_SLEEP_SECS = 60  # seconds to sleep between rapidfire loops

LAUNCHPAD_LOC = None  # where to find the my_launchpad.yaml file
FWORKER_LOC = None  # where to find the my_fworker.yaml file
QUEUEADAPTER_LOC = None  # where to find the my_qadapter.yaml file

CONFIG_FILE_DIR = '.'  # directory containing config files (if not individually set)

ROCKET_STREAM_LOGLEVEL = "INFO"  # the streaming log level of the rocket.launcher logger

QSTAT_FREQUENCY = 50  # set this higher to avoid qstats, lower to alwas

ALWAYS_CREATE_NEW_BLOCK = False  # always create new block on queue launcher call

TEMPLATE_DIR = None  # default template dir for TemplateWriterTask

REMOVE_USELESS_DIRS = True  # deletes empty launch dir if _launch_dir set

DS_PASSWORD = b'1234'  # dummy password to access DataServer

STORE_PACKING_INFO = True  # automatically add job packing info to stored_data

PW_CHECK_NUM = 10  # number of entries that can be modified in single lpad command w/o password

TRACKER_LINES = 25  # number of lines to return in Tracker

SORT_FWS = ''  # sort equal priority FWs? "FILO" or "FIFO".

ENCODE_MONTY = True  # detect and use Monty-style as_dict()

DECODE_MONTY = True  # detect and use Monty-style from_dict() with @class and @module

EXCEPT_DETAILS_ON_RERUN = False  # add exception details to the spec when rerunning the FW

WEBSERVER_HOST = "127.0.0.1"  # default host on which the Flask web server runs

WEBSERVER_PORT = 5000  # default port on which the Flask web server runs

WEBSERVER_PERFWARNINGS = False # enable performance-related warnings

# value of socketTimeoutMS when connection to mongoDB.  See pymongo official
# documentation http://api.mongodb.org/python/current/api/pymongo/mongo_client.html
MONGO_SOCKET_TIMEOUT_MS = 5 * 60 * 1000


def override_user_settings():
    module_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(module_dir)  # FW root dir

    config_paths = []

    test_paths = [os.getcwd(), os.path.join(os.path.expanduser('~'), ".fireworks"), root_dir]

    for p in test_paths:
        fp = os.path.join(p, 'FW_config.yaml')
        if fp not in config_paths and os.path.exists(fp):
            config_paths.append(fp)

    if "FW_CONFIG_FILE" in os.environ and os.environ["FW_CONFIG_FILE"] not in\
            config_paths:
        config_paths.append(os.environ["FW_CONFIG_FILE"])

    config_paths = config_paths or [os.path.join(
        os.path.expanduser('~'), ".fireworks", 'FW_config.yaml')]

    if len(config_paths) > 1:
        print("Found many potential paths for {}: {}\nChoosing as default: {}"
              .format("FW_CONFIG_FILE", config_paths, config_paths[0]))

    if os.path.exists(config_paths[0]):
        overrides = loadfn(config_paths[0])
        for key, v in overrides.items():
            if key == 'ADD_USER_PACKAGES':
                USER_PACKAGES.extend(v)
            elif key == 'ECHO_TEST':
                print(v)
            elif key not in globals():
                raise ValueError('Invalid FW_config file has unknown parameter: {}'.format(key))
            else:
                globals()[key] = v

    for k in ["LAUNCHPAD_LOC", "FWORKER_LOC", "QUEUEADAPTER_LOC"]:
        if globals().get(k, None) is None:
            fname = "my_qadapter.yaml" if k == "QUEUEADAPTER_LOC" else \
                "my_{}.yaml".format(k.split("_")[0].lower())
            m_paths = []
            if os.path.realpath(CONFIG_FILE_DIR) not in test_paths:
                test_paths.insert(0, CONFIG_FILE_DIR)
            for p in test_paths:
                fp = os.path.join(p, fname)
                if os.path.exists(fp) and fp not in m_paths:
                    m_paths.append(fp)

            if len(m_paths) > 1:
                print("Found many potential paths for {}: {}\nChoosing as default: {}"
                      .format(k, m_paths, m_paths[0]))

            if len(m_paths) > 0:
                globals()[k] = m_paths[0]


override_user_settings()


def config_to_dict():
    d = {}
    for k, v in globals().items():
        if k.upper() == k and k != "NEGATIVE_FWID_CTR":
            d[k] = v
    return d


def write_config(path=None):
    path = os.path.join(os.path.expanduser('~'), ".fireworks", 'FW_config.yaml') if path is None else path
    dumpfn(config_to_dict(), path)


@singleton
class FWData(object):
    """
    This class stores data that a Firetask might want to access, e.g. to see the runtime params
    """

    def __init__(self):
        self.MULTIPROCESSING = None  # default single process framework
        self.NODE_LIST = None  # the node list for sub jobs
        self.SUB_NPROCS = None  # the number of process of the sub job
        self.DATASERVER = None  # the shared object manager
        self.Running_IDs = None
