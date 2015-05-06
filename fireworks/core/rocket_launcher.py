# coding: utf-8

from __future__ import unicode_literals

"""
This module contains methods for launching Rockets, both singly and in rapid-fire mode
"""

import os
import time
from fireworks.fw_config import RAPIDFIRE_SLEEP_SECS
from fireworks.core.fworker import FWorker
from fireworks.core.rocket import Rocket
from fireworks.utilities.fw_utilities import get_fw_logger, create_datestamp_dir, log_multi

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 22, 2013'


def launch_rocket(launchpad, fworker=None, fw_id=None, strm_lvl='INFO'):
    """
    Run a single rocket in the current directory
    :param launchpad: (LaunchPad)
    :param fworker: (FWorker)
    :param fw_id: (int) if set, a particular Firework to run
    :param strm_lvl: (str) level at which to output logs to stdout
    """
    fworker = fworker if fworker else FWorker()
    l_dir = launchpad.get_logdir() if launchpad else None
    l_logger = get_fw_logger('rocket.launcher', l_dir=l_dir, stream_level=strm_lvl)

    log_multi(l_logger, 'Launching Rocket')
    rocket = Rocket(launchpad, fworker, fw_id)
    rocket_ran = rocket.run()
    log_multi(l_logger, 'Rocket finished')
    return rocket_ran


def rapidfire(launchpad, fworker=None, m_dir=None, nlaunches=0, max_loops=-1, sleep_time=None, strm_lvl='INFO'):
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

    sleep_time = sleep_time if sleep_time else RAPIDFIRE_SLEEP_SECS
    curdir = m_dir if m_dir else os.getcwd()
    l_logger = get_fw_logger('rocket.launcher', l_dir=launchpad.get_logdir(), stream_level=strm_lvl)
    nlaunches = -1 if nlaunches == 'infinite' else int(nlaunches)
    fworker = fworker if fworker else FWorker()

    num_launched = 0
    num_loops = 0

    while num_loops != max_loops:
        skip_check = False  # this is used to speed operation
        while skip_check or launchpad.run_exists(fworker):
            os.chdir(curdir)
            launcher_dir = create_datestamp_dir(curdir, l_logger, prefix='launcher_')
            os.chdir(launcher_dir)
            rocket_ran = launch_rocket(launchpad, fworker, strm_lvl=strm_lvl)
            if rocket_ran:
                num_launched += 1
            elif not os.listdir(launcher_dir):
                # remove the empty shell of a directory
                os.chdir(curdir)
                os.rmdir(launcher_dir)
            if num_launched == nlaunches:
                break
            if launchpad.run_exists(fworker):
                skip_check = True  # don't wait, pull the next FW right away
            else:
                time.sleep(0.15)  # add a small amount of buffer breathing time for DB to refresh in case we have a dynamic WF
                skip_check = False
        if num_launched == nlaunches or nlaunches == 0:
            break
        log_multi(l_logger, 'Sleeping for {} secs'.format(sleep_time))
        time.sleep(sleep_time)
        num_loops += 1
        log_multi(l_logger, 'Checking for FWs to run...'.format(sleep_time))
    os.chdir(curdir)
