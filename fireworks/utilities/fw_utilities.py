#!/usr/bin/env python
from bz2 import BZ2File
from gzip import GzipFile

import logging
import datetime
from multiprocessing.managers import BaseManager, DictProxy
import string
import sys
import os
import traceback
import socket
import multiprocessing

from fireworks.core.fw_config import FWConfig, FWData


__author__ = 'Anubhav Jain, Xiaohui Qu'
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
        m = DataServer(address=('127.0.0.1', 0), authkey=FWConfig().DS_PASSWORD)  # random port
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


def reverse_readline(m_file, blk_size=4096, max_mem=4000000):
    """
    Generator method to read a file line-by-line, but backwards. This allows
    one to efficiently get data at the end of a file.

    Based on code by Peter Astrand <astrand@cendio.se>, using modifications by
    Raymond Hettinger and Kevin German.
    http://code.activestate.com/recipes/439045-read-a-text-file-backwards
    -yet-another-implementat/

    Reads file forwards and reverses in memory for files smaller than the
    max_mem parameter, or for gzip files where reverse seeks are not supported.

    Files larger than max_mem are dynamically read backwards.

    Args:
        m_file:
            File stream to read (backwards)
        blk_size:
            The buffer size. Defaults to 4096.
        max_mem:
            The maximum amount of memory to involve in this operation. This is
            used to determine when to reverse a file in-memory versus seeking
            portions of a file. For bz2 files, this sets the maximum block
            size.

    Returns:
        Generator that returns lines from the file. Similar behavior to the
        file.readline() method, except the lines are returned from the back
        of the file.
    """

    file_size = os.path.getsize(m_file.name)

    # If the file size is within our desired RAM use, just reverse it in memory
    # GZip files must use this method because there is no way to negative seek
    if file_size < max_mem or isinstance(m_file, GzipFile):
        for line in reversed(m_file.readlines()):
            yield line.rstrip()
    else:
        if isinstance(m_file, BZ2File):
            # for bz2 files, seeks are expensive. It is therefore in our best
            # interest to maximize the blk_size within limits of desired RAM
            # use.
            blk_size = min(max_mem, file_size)

        buf = ""
        m_file.seek(0, 2)
        lastchar = m_file.read(1)
        trailing_newline = (lastchar == "\n")

        while 1:
            newline_pos = buf.rfind("\n")
            pos = m_file.tell()
            if newline_pos != -1:
                # Found a newline
                line = buf[newline_pos + 1:]
                buf = buf[:newline_pos]
                if pos or newline_pos or trailing_newline:
                    line += "\n"
                yield line
            elif pos:
                # Need to fill buffer
                toread = min(blk_size, pos)
                m_file.seek(pos - toread, 0)
                buf = m_file.read(toread) + buf
                m_file.seek(pos - toread, 0)
                if pos == toread:
                    buf = "\n" + buf
            else:
                # Start-of-file
                return


def explicit_serialize(o):
    o._fw_name = '{{'+o.__module__+'.'+o.__name__+'}}'
    return o