#!/usr/bin/env python

"""
This module contains methods for launching Rockets, both singly and in rapid-fire mode
"""

import os
import time
from fireworks.core.fw_config import FWConfig
from fireworks.core.rocket import Rocket
from fireworks.utilities.fw_utilities import get_fw_logger, create_datestamp_dir
import multiprocessing

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 22, 2013'


def launch_rocket(launchpad, fworker, fw_id=None, strm_lvl='INFO'):
    """
    Run a single rocket in the current directory
    :param launchpad: (LaunchPad)
    :param fworker: (FWorker)
    :param fw_id: (int) if set, a particular FireWork to run
    :param strm_lvl: (str) level at which to output logs to stdout
    """
    l_logger = get_fw_logger('rocket.launcher', l_dir=launchpad.get_logdir(), stream_level=strm_lvl)

    fw_conf = FWConfig()
    if not fw_conf.MULTIPROCESSING:
        l_logger.info('Launching Rocket')
    else:
        l_logger.info(multiprocessing.current_process().name + ": Launching Rocket")
    rocket = Rocket(launchpad, fworker, fw_id)
    rocket.run()
    if not fw_conf.MULTIPROCESSING:
        l_logger.info('Rocket finished')
    else:
        l_logger.info(multiprocessing.current_process().name + ": Rocket finished")


def rapidfire(launchpad, fworker, m_dir=None, nlaunches=0, max_loops=-1, sleep_time=None, strm_lvl='INFO'):
    """
    Keeps running Rockets in m_dir until we reach an error. Automatically creates subdirectories for each Rocket.
    Usually stops when we run out of FireWorks from the LaunchPad.

    :param launchpad: (LaunchPad)
    :param fworker: (FWorker object)
    :param m_dir: (str) the directory in which to loop Rocket running
    :param nlaunches: (int) 0 means 'until completion', -1 or "infinite" means to loop forever
    :param max_loops: (int) maximum number of loops
    :param sleep_time: (int) secs to sleep between rapidfire loop iterations
    :param strm_lvl: (str) level at which to output logs to stdout
    """

    sleep_time = sleep_time if sleep_time else FWConfig().RAPIDFIRE_SLEEP_SECS
    curdir = m_dir if m_dir else os.getcwd()
    l_logger = get_fw_logger('rocket.launcher', l_dir=launchpad.get_logdir(), stream_level=strm_lvl)
    nlaunches = -1 if nlaunches == 'infinite' else int(nlaunches)

    num_launched = 0
    num_loops = 0

    fw_conf = FWConfig()
    while num_loops != max_loops:
        if fw_conf.MULTIPROCESSING:
            fw_conf.PROCESS_LOCK.acquire()
        while launchpad.run_exists(fworker):
            os.chdir(curdir)
            launcher_dir = create_datestamp_dir(curdir, l_logger, prefix='launcher_')
            os.chdir(launcher_dir)
            launch_rocket(launchpad, fworker, strm_lvl=strm_lvl)
            num_launched += 1
            if fw_conf.MULTIPROCESSING:
                fw_conf.PROCESS_LOCK.acquire()
            if num_launched == nlaunches:
                break
            time.sleep(0.15)  # add a small amount of buffer breathing time for DB to refresh, etc.
        if fw_conf.MULTIPROCESSING:
            fw_conf.PROCESS_LOCK.release()
        if num_launched == nlaunches or nlaunches == 0:
            break
        if not fw_conf.MULTIPROCESSING:
            l_logger.info('Sleeping for {} secs'.format(sleep_time))
        else:
            l_logger.info(multiprocessing.current_process().name + ": " +'Sleeping for {} secs'.format(sleep_time))
        time.sleep(sleep_time)
        num_loops += 1
        if not fw_conf:
            l_logger.info('Checking for FWs to run...'.format(sleep_time))
        else:
            l_logger.info(multiprocessing.current_process().name + ": " +
                          'Checking for FWs to run...'.format(sleep_time))