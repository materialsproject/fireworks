import os
import time
from fireworks.core.rocket import Rocket
from fireworks.utilities.fw_utilities import get_fw_logger, create_datestamp_dir

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 22, 2013'


def launch_rocket(launchpad, fworker, logdir=None, strm_lvl=None):
    """
    Run a single rocket in the current directory
    :param launchpad: a LaunchPad object
    :param fworker: a FWorker object
    """
    l_logger = get_fw_logger('rocket.launcher', l_dir=logdir, stream_level=strm_lvl)
    l_logger.info('Launching Rocket')
    rocket = Rocket(launchpad, fworker)
    rocket.run()
    l_logger.info('Rocket finished')


def rapidfire(launchpad, fworker, m_dir=None, logdir=None, strm_lvl=None, infinite=False, sleep_time=60):
    """
    Keeps running Rockets in m_dir until we reach an error. Automatically creates subdirectories for each Rocket.
    Usually stops when we run out of FireWorks from the LaunchPad.

    :param launchpad: a LaunchPad object
    :param fworker: a FWorker object
    :param m_dir: the directory in which to loop Rocket running
    """
    curdir = m_dir if m_dir else os.getcwd()
    # initialize logger
    l_logger = get_fw_logger('rocket.launcher', l_dir=logdir, stream_level=strm_lvl)

    while True:
        while launchpad.run_exists():
            os.chdir(curdir)
            launcher_dir = create_datestamp_dir(curdir, l_logger, prefix='launcher_')
            os.chdir(launcher_dir)
            launch_rocket(launchpad, fworker, logdir, strm_lvl)
            time.sleep(0.05)  # delay; might not be needed, just a safeguard to keep the script from tripping on itself
        if not infinite:
            break
        l_logger.info('Sleeping for {} secs'.format(sleep_time))
        time.sleep(sleep_time)
        l_logger.info('Checking for FWs to run...'.format(sleep_time))


