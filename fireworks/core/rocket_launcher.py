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


def launch_rocket(launchpad, fworker):
    """
    Run a single rocket in the current directory
    :param launchpad: a LaunchPad object
    :param fworker: a FWorker object
    """
    rocket = Rocket(launchpad, fworker)
    rocket.run()


def loop_rocket_run(launchpad, fworker, m_dir=None):
    """
    Keeps running Rockets in m_dir until we reach an error. Automatically creates subdirectories for each Rocket.
    Usually stops when we run out of FireWorks from the LaunchPad.

    :param launchpad: a LaunchPad object
    :param fworker: a FWorker object
    :param m_dir: the directory in which to loop Rocket running
    """
    curdir = m_dir if m_dir else os.getcwd()
    # initialize logger
    l_logger = get_fw_logger('rocket.loop', curdir)
    while True:
        os.chdir(curdir)
        launcher_dir = create_datestamp_dir(curdir, l_logger, prefix='launcher_')
        os.chdir(launcher_dir)
        l_logger.info('Submitting Rocket')
        launch_rocket(launchpad, fworker)
        l_logger.info('Rocket finished')
        time.sleep(0.25)  # delay; might not be needed, just a safeguard to keep the script from tripping on itself