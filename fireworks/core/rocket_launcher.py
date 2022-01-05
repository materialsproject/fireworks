"""
This module contains methods for launching Rockets, both singly and in rapid-fire mode.
"""

import os
import time
from datetime import datetime

from fireworks.core.fworker import FWorker
from fireworks.core.rocket import Rocket
from fireworks.fw_config import FWORKER_LOC, RAPIDFIRE_SLEEP_SECS
from fireworks.utilities.fw_utilities import (
    create_datestamp_dir,
    get_fw_logger,
    log_multi,
    redirect_local,
)

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 22, 2013"


def get_fworker(fworker):
    if fworker:
        my_fwkr = fworker
    elif FWORKER_LOC:
        my_fwkr = FWorker.from_file(FWORKER_LOC)
    else:
        my_fwkr = FWorker()
    return my_fwkr


def launch_rocket(launchpad, fworker=None, fw_id=None, strm_lvl="INFO", pdb_on_exception=False):
    """
    Run a single rocket in the current directory.

    Args:
        launchpad (LaunchPad)
        fworker (FWorker)
        fw_id (int): if set, a particular Firework to run
        strm_lvl (str): level at which to output logs to stdout
        pdb_on_exception (bool): if set to True, python will start
            the debugger on a firework exception

    Returns:
        bool
    """
    fworker = get_fworker(fworker)
    l_dir = launchpad.get_logdir() if launchpad else None
    l_logger = get_fw_logger("rocket.launcher", l_dir=l_dir, stream_level=strm_lvl)

    log_multi(l_logger, "Launching Rocket")
    rocket = Rocket(launchpad, fworker, fw_id)
    rocket_ran = rocket.run(pdb_on_exception=pdb_on_exception)
    log_multi(l_logger, "Rocket finished")
    return rocket_ran


def rapidfire(
    launchpad,
    fworker=None,
    m_dir=None,
    nlaunches=0,
    max_loops=-1,
    sleep_time=None,
    strm_lvl="INFO",
    timeout=None,
    local_redirect=False,
    pdb_on_exception=False,
):
    """
    Keeps running Rockets in m_dir until we reach an error. Automatically creates subdirectories
    for each Rocket. Usually stops when we run out of FireWorks from the LaunchPad.

    Args:
        launchpad (LaunchPad)
        fworker (FWorker object)
        m_dir (str): the directory in which to loop Rocket running
        nlaunches (int): 0 means 'until completion', -1 or "infinite" means to loop until max_loops
        max_loops (int): maximum number of loops (default -1 is infinite)
        sleep_time (int): secs to sleep between rapidfire loop iterations
        strm_lvl (str): level at which to output logs to stdout
        timeout (int): of seconds after which to stop the rapidfire process
        local_redirect (bool): redirect standard input and output to local file
    """

    sleep_time = sleep_time if sleep_time else RAPIDFIRE_SLEEP_SECS
    curdir = m_dir if m_dir else os.getcwd()
    l_logger = get_fw_logger("rocket.launcher", l_dir=launchpad.get_logdir(), stream_level=strm_lvl)
    nlaunches = -1 if nlaunches == "infinite" else int(nlaunches)
    fworker = get_fworker(fworker)

    num_launched = 0
    start_time = datetime.now()
    num_loops = 0

    def time_ok():
        # has the rapidfire run timed out?
        return timeout is None or (datetime.now() - start_time).total_seconds() < timeout

    while num_loops != max_loops and time_ok():
        skip_check = False  # this is used to speed operation
        while (skip_check or launchpad.run_exists(fworker)) and time_ok():
            os.chdir(curdir)
            launcher_dir = create_datestamp_dir(curdir, l_logger, prefix="launcher_")
            os.chdir(launcher_dir)
            if local_redirect:
                with redirect_local():
                    rocket_ran = launch_rocket(launchpad, fworker, strm_lvl=strm_lvl, pdb_on_exception=pdb_on_exception)
            else:
                rocket_ran = launch_rocket(launchpad, fworker, strm_lvl=strm_lvl, pdb_on_exception=pdb_on_exception)

            if rocket_ran:
                num_launched += 1
            elif not os.listdir(launcher_dir):
                # remove the empty shell of a directory
                os.chdir(curdir)
                os.rmdir(launcher_dir)
            if nlaunches > 0 and num_launched == nlaunches:
                break
            if launchpad.run_exists(fworker):
                skip_check = True  # don't wait, pull the next FW right away
            else:
                # add a small amount of buffer breathing time for DB to refresh in case we have a dynamic WF
                time.sleep(0.15)
                skip_check = False
        if nlaunches == 0:
            if not launchpad.future_run_exists(fworker):
                break
        elif num_launched == nlaunches:
            break
        log_multi(l_logger, f"Sleeping for {sleep_time} secs")
        time.sleep(sleep_time)
        num_loops += 1
        log_multi(l_logger, "Checking for FWs to run...")
    os.chdir(curdir)
