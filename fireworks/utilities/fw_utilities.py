#!/usr/bin/env python

import logging
import sys
import os
import traceback
from fireworks.core.fw_constants import FW_LOGGING_FORMATTER

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'


def get_fw_logger(name, l_dir='.', file_levels=('DEBUG', 'ERROR'), stream_level='DEBUG', formatter=FW_LOGGING_FORMATTER, clear_logs=False):
    '''
    Convenience method to return a logger.
    
    :param name: name of the logger that sets the groups, e.g. 'group1.set2'
    :param l_dir: the directory to put the log file
    :param file_levels: iterable describing level(s) to log to file(s). default: ('DEBUG', 'ERROR')
    :param stream_level: level to log to standard output. default: 'DEBUG'
    :param formatter: logging format. default: FW_LOGGING_FORMATTER
    :param clear_logs: whether to clear the logger with the same name
    '''

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # anything debug and above passes through to the handler level
            
    # add handlers for the file_levels
    for lvl in file_levels:
        f_name = os.path.join(l_dir, name.replace('.', '_') + '-' + lvl.lower() + '.log')
        mode = 'w' if clear_logs else 'a'
        fh = logging.FileHandler(f_name, mode=mode)
        fh.setLevel(getattr(logging, lvl))
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    # add stream handler
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setLevel(getattr(logging, stream_level))
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
    return logger


def log_fancy(m_logger, log_lvl, msgs, add_traceback=False):
    '''
    A wrapper around the logger messages useful for multi-line logs.
    Just helps to group log messages by adding a fancy border around it,
    which hopefully enhances readability of log lines meant to be
    read together as a unit.
    
    :param m_logger: The logger object
    :param log_lvl: The level to log at
    :param msgs: a String or iterable of Strings
    :param add_traceback: add traceback text, useful when logging exceptions (default False)
    '''
    
    if isinstance(msgs, basestring):
        msgs = [msgs]
        
    _log_fnc = getattr(m_logger, log_lvl.lower())

    _log_fnc('----|vvv|----')
    _log_fnc('\n'.join(msgs))
    if add_traceback:
        _log_fnc(traceback.format_exc())
    _log_fnc('----|^^^|----')


def log_exception(m_logger, msgs):
    '''
    A shortcut wrapper around log_fancy for exceptions
    :param m_logger: The logger object
    :param msgs: An iterable of Strings, will be joined by newlines
    '''
    return log_fancy(m_logger, "error", msgs, add_traceback=True)
