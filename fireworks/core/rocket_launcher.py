import os
import time
from fireworks.core.fworker import FWorker
from fireworks.core.rocket import Rocket
from fireworks.utilities.fw_utilities import get_fw_logger, create_datestamp_dir

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 22, 2013'


def launch_rocket(launchpad, fworker=None, logdir=None, strm_lvl=None, fw_id=None):
    """
    Run a single rocket in the current directory
    :param launchpad: a LaunchPad object
    :param fworker: a FWorker object
    """
    fworker = fworker if fworker else FWorker()
    l_logger = get_fw_logger('rocket.launcher', l_dir=logdir, stream_level=strm_lvl)
    l_logger.info('Launching Rocket')
    rocket = Rocket(launchpad, fworker, fw_id)
    rocket.run()
    l_logger.info('Rocket finished')


def rapidfire(launchpad, fworker=None, m_dir=None, logdir=None, strm_lvl=None, nlaunches=0, sleep_time=60, max_loops=-1):
    """
    Keeps running Rockets in m_dir until we reach an error. Automatically creates subdirectories for each Rocket.
    Usually stops when we run out of FireWorks from the LaunchPad.

    :param launchpad: a LaunchPad object
    :param fworker: a FWorker object
    :param m_dir: the directory in which to loop Rocket running
    :param nlaunches: 0 means 'until completion', -1 means 'infinity'
    """
    curdir = m_dir if m_dir else os.getcwd()
    fworker = fworker if fworker else FWorker()
    # initialize logger
    l_logger = get_fw_logger('rocket.launcher', l_dir=logdir, stream_level=strm_lvl)
    nlaunches = -1 if nlaunches == 'infinite' else int(nlaunches)

    # TODO: wrap in try-except. Use log_exception for exceptions EXCEPT running out of jobs.
    # TODO: always chdir() back to curdir when finished...then delete cruft from MongoTests
    num_launched = 0
    num_loops = 0
    while num_loops != max_loops:
        while launchpad.run_exists():
            os.chdir(curdir)
            launcher_dir = create_datestamp_dir(curdir, l_logger, prefix='launcher_')
            os.chdir(launcher_dir)
            launch_rocket(launchpad, fworker, logdir, strm_lvl)
            num_launched += 1
            if num_launched == nlaunches:
                break
            time.sleep(0.1)  # add a small amount of buffer breathing time for DB to refresh, etc.
        if num_launched == nlaunches or nlaunches == 0:
            break
        l_logger.info('Sleeping for {} secs'.format(sleep_time))
        time.sleep(sleep_time)
        num_loops += 1
        l_logger.info('Checking for FWs to run...'.format(sleep_time))


