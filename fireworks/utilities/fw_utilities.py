# coding: utf-8

import logging
import datetime
from multiprocessing.managers import BaseManager, DictProxy
import string
import sys
import os
import traceback
import socket
import multiprocessing
import errno

from fireworks.fw_config import FWData, FW_BLOCK_FORMAT, DS_PASSWORD, \
    FW_LOGGING_FORMAT


__author__ = 'Anubhav Jain, Xiaohui Qu'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'

PREVIOUS_STREAM_LOGGERS = []  # contains the name of loggers that have already been initialized
PREVIOUS_FILE_LOGGERS = []  # contains the name of file loggers that have already been initialized
DEFAULT_FORMATTER = logging.Formatter(FW_LOGGING_FORMAT)


def get_fw_logger(name, l_dir=None, file_levels=('DEBUG', 'ERROR'),
                  stream_level='DEBUG', formatter=DEFAULT_FORMATTER,
                  clear_logs=False):
    """
    Convenience method to return a logger.

    :param name: name of the logger that sets the groups, e.g. 'group1.set2'
    :param l_dir: the directory to put the log file
    :param file_levels: iterable describing level(s) to log to file(s). default: ('DEBUG', 'ERROR')
    :param stream_level: level to log to standard output. default: 'DEBUG'
    :param formatter: logging format. default: FW_LOGGING_FORMATTER
    :param clear_logs: whether to clear the logger with the same name
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # anything debug and above passes through to the handler level

    stream_level = stream_level if stream_level else 'CRITICAL'
    # add handlers for the file_levels
    if l_dir:
        for lvl in file_levels:
            f_name = os.path.join(l_dir, name.replace('.', '_') + '-' + lvl.lower() + '.log')
            mode = 'w' if clear_logs else 'a'
            fh = logging.FileHandler(f_name, mode=mode)
            fh.setLevel(getattr(logging, lvl))
            fh.setFormatter(formatter)
            if f_name not in PREVIOUS_FILE_LOGGERS:
                logger.addHandler(fh)
                PREVIOUS_FILE_LOGGERS.append(f_name)

    if (name, stream_level) not in PREVIOUS_STREAM_LOGGERS:
        # add stream handler
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setLevel(getattr(logging, stream_level))
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        PREVIOUS_STREAM_LOGGERS.append((name, stream_level))

    return logger


def log_multi(m_logger, msg, log_lvl='info'):
    """
    :param m_logger: (logger) The logger object
    :param msg: (str) a String to log
    :param log_lvl: (str) The level to log at
    """
    _log_fnc = getattr(m_logger, log_lvl.lower())
    if FWData().MULTIPROCESSING:
        _log_fnc("{} : ({})".format(msg, multiprocessing.current_process().name))
    else:
        _log_fnc(msg)


def log_fancy(m_logger, msgs, log_lvl='info', add_traceback=False):
    """
    A wrapper around the logger messages useful for multi-line logs.
    Helps to group log messages by adding a fancy border around it,
    which enhances readability of log lines meant to be read
    as a unit.

    :param m_logger: (logger) The logger object
    :param log_lvl: (str) The level to log at
    :param msgs: ([str]) a String or iterable of Strings
    :param add_traceback: (bool) add traceback text, useful when logging exceptions (default False)
    """

    if isinstance(msgs, basestring):
        msgs = [msgs]

    _log_fnc = getattr(m_logger, log_lvl.lower())

    _log_fnc('----|vvv|----')
    _log_fnc('\n'.join(msgs))
    if add_traceback:
        _log_fnc(traceback.format_exc())
    _log_fnc('----|^^^|----')


def log_exception(m_logger, msgs):
    """
    A shortcut wrapper around log_fancy for exceptions

    :param m_logger: (logger) The logger object
    :param msgs: ([str]) String or iterable of Strings, will be joined by newlines
    """
    return log_fancy(m_logger, msgs, 'error', add_traceback=True)


def create_datestamp_dir(root_dir, l_logger, prefix='block_'):
    """
    Internal method to create a new block or launcher directory. \
    The dir name is based on the time and the FW_BLOCK_FORMAT

    :param root_dir: directory to create the new dir in
    :param l_logger: the logger to use
    :param prefix: the prefix for the new dir, default="block_"
    """

    def get_path():
        time_now = datetime.datetime.utcnow().strftime(FW_BLOCK_FORMAT)
        block_path = prefix + time_now
        return os.path.join(root_dir, block_path)
    ctn = 0
    max_try = 10
    full_path = None
    while full_path is None:
        full_path = get_path()
        if os.path.exists(full_path):
            full_path = None
            import time
            import random
            time.sleep(random.random()/3+0.1)
            continue
        else:
            try:
                os.mkdir(full_path)
                break
            except OSError as e:
                if ctn > max_try or e.errno != errno.EEXIST:
                    raise e
                ctn += 1
                full_path = None
                continue

    l_logger.info('Created new dir {}'.format(full_path))
    return full_path


_g_ip, _g_host = None, None

def get_my_ip():
    global _g_ip
    if _g_ip is None:
        try:
            _g_ip = socket.gethostbyname(socket.gethostname())
        except:
            _g_ip = '127.0.0.1'
    return _g_ip


def get_my_host():
    global _g_host
    if _g_host is None:
        _g_host = socket.gethostname()
    return _g_host


def get_slug(m_str):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    m_str = ''.join(c for c in m_str if c in valid_chars)
    return m_str.replace(' ', '_')


class DataServer(BaseManager):
    """
    Provide a server that can host shared objects between multiprocessing
    Processes (that normally can't share data). For example, a common LaunchPad is
    shared between processes and pinging launches is coordinated to limit DB hits.
    """

    @classmethod
    def setup(cls, launchpad):
        """
        :param launchpad: (LaunchPad) object
        :return:
        """
        DataServer.register('LaunchPad', callable=lambda: launchpad)
        DataServer.register('Running_IDs', callable=lambda: {}, proxytype=DictProxy)
        m = DataServer(address=('127.0.0.1', 0), authkey=DS_PASSWORD)  # random port
        m.start()
        return m


class NestedClassGetter(object):
    """
    Used to help pickle inner classes, e.g. see Workflow.Links
    When called with the containing class as the first argument,
    and the name of the nested class as the second argument,
    returns an instance of the nested class.
    """
    def __call__(self, containing_class, class_name):
        nested_class = getattr(containing_class, class_name)
        # return an instance of a nested_class. Some more intelligence could be
        # applied for class construction if necessary.
        # To support for Pickling of Workflow.Links
        return nested_class()


def explicit_serialize(o):
    module_name = o.__module__
    if module_name == '__main__':
        import __main__
        module_name = os.path.splitext(os.path.basename(__main__.__file__))[0]
    o._fw_name = '{{%s.%s}}' % (module_name, o.__name__)
    return o