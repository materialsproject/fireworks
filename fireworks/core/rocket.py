#!/usr/bin/env python

"""
TODO: add docs
"""
import os
import traceback
import json
from fireworks.core.firework import FWAction
from fireworks.core.fw_constants import DATETIME_HANDLER, PRINT_FW_JSON
from fireworks.utilities.fw_utilities import get_host_ip

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

    def __init__(self, launchpad, fworker, fw_id):
        """
        
        :param launchpad: A LaunchPad object for interacting with the FW database
        :param fworker: A FWorker object describing the computing resource
        """
        self.launchpad = launchpad
        self.fworker = fworker
        self.fw_id = fw_id

    def run(self):
        """
        Run the rocket (actually check out a job from the database and execute it)
        """

        lp = self.launchpad
        host, ip = get_host_ip()
        launch_dir = os.path.abspath(os.getcwd())

        # check a FW job out of the launchpad
        m_fw, launch_id = lp._checkout_fw(self.fworker, host, ip, launch_dir)
        if not m_fw:
            raise ValueError("No FireWorks are ready to run and match query! {}".format(self.fworker.query))

        if PRINT_FW_JSON:
            with open('fw.json', 'w') as f:
                f.write(json.dumps(m_fw.to_dict(), default=DATETIME_HANDLER))

        # execute the script inside the spec
        # TODO: bind monitors, etc...
        # add fw_dict stuff
        # add checkpoint stuff
        # add heartbeat
        # lots of stuff to add!
        # update the number of tasks completed in the launch after every task
        # TODO: support stored_dict update() rather than overwrite

        for my_task in m_fw.tasks:
            try:
                m_action = my_task.run_task(m_fw)
                # TODO: allow a program to write the decision to a file...
                if not m_action:
                    m_action = FWAction('CONTINUE')

                if m_action.command != 'CONTINUE':
                    break;
            except:
                m_action = FWAction('DEFUSE', {'_message': 'runtime error during task', '_task': my_task.to_dict(), '_exception': traceback.format_exc()})

        # perform finishing operation
        lp._complete_launch(launch_id, m_action)