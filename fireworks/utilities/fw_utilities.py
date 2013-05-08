#!/usr/bin/env python

import logging
import datetime
import string
import sys
import os
import traceback
import socket
from fireworks.core.fw_config import FWConfig

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'

PREVIOUS_STREAM_LOGGERS = []  # contains the name of loggers that have already been initialized
PREVIOUS_FILE_LOGGERS = []  # contains the name of file loggers that have already been initialized
DEFAULT_FORMATTER = logging.Formatter(FWConfig().FW_LOGGING_FORMAT)


def get_fw_logger(name, l_dir=None, file_levels=('DEBUG', 'ERROR'), stream_level='DEBUG', formatter=DEFAULT_FORMATTER,
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


def log_fancy(m_logger, log_lvl, msgs, add_traceback=False):
    """
    A wrapper around the logger messages useful for multi-line logs.
    Helps to group log messages by adding a fancy border around it,
    which enhances readability of log lines meant to be read
    as a unit.
    
    :param m_logger: The logger object
    :param log_lvl: The level to log at
    :param msgs: a String or iterable of Strings
    :param add_traceback: add traceback text, useful when logging exceptions (default False)
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
    
    :param m_logger: The logger object
    :param msgs: An iterable of Strings, will be joined by newlines
    """
    return log_fancy(m_logger, 'error', msgs, add_traceback=True)


def create_datestamp_dir(root_dir, l_logger, prefix='block_'):
    """
    Internal method to create a new block or launcher directory. \
    The dir name is based on the time and the FW_BLOCK_FORMAT

    :param root_dir: directory to create the new dir in
    :param l_logger: the logger to use
    :param prefix: the prefix for the new dir, default="block_"
    """

    time_now = datetime.datetime.utcnow().strftime(FWConfig().FW_BLOCK_FORMAT)
    block_path = prefix + time_now
    full_path = os.path.join(root_dir, block_path)
    os.mkdir(full_path)
    l_logger.info('Created new dir {}'.format(full_path))
    return full_path

def get_my_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return '127.0.0.1'


def get_my_host():
    return socket.gethostname()


def get_slug(m_str):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    m_str = ''.join(c for c in m_str if c in valid_chars)
    return m_str.replace(' ', '_')