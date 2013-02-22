#!/usr/bin/env python

"""
TODO: add docs
"""
import os
import socket
import simplejson as json
import time
from fireworks.core.fw_constants import DATETIME_HANDLER
from fireworks.utilities.fw_utilities import create_datestamp_dir, get_fw_logger

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'


class Rocket():
    """
    The Rocket fetches a workflow step from the FireWorks database and executes it.
    """

    def __init__(self, launchpad, fworker):
        """
        
        :param launchpad: A LaunchPad object for interacting with the FW database
        :param fworker: A FWorker object describing the computing resource
        """
        self.launchpad = launchpad
        self.fworker = fworker

    def run(self):
        """
        Run the rocket (actually check out a job from the database and execute it)
        """

        lp = self.launchpad

        host = socket.gethostname()
        ip = socket.gethostbyname(socket.gethostname())
        launch_dir = os.path.abspath(os.getcwd())

        # check a FW job out of the launchpad
        m_fw, launch_id = lp._checkout_fw(self.fworker, host, ip, launch_dir)
        if not m_fw:
            raise ValueError("No FireWorks are ready to run and match query! {}".format(self.fworker.query))

        with open('fw.json', 'w') as f:
            f.write(json.dumps(m_fw.to_dict(), default=DATETIME_HANDLER))

        # execute the script inside the spec
        # TODO: support lists, native Python code, bind monitors, etc...
        # add fw_dict stuff
        # add checkpoint stuff
        # add heartbeat
        # lots of stuff to add!

        for my_task in m_fw.tasks:
            m_decision = my_task.run_task(m_fw)

        # TODO: continue on to next script if:
        # - it exists
        # - no fw_output.json
        # no output dict()

        # TODO: add more useful information in the launch!

        # perform finishing operation
        lp._complete_launch(m_fw, launch_id)


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
        rocket = Rocket(launchpad, fworker)
        rocket.run()
        l_logger.info('Rocket finished')
        time.sleep(0.25)  # delay; might not be needed, just a safeguard to keep the script from tripping on itself