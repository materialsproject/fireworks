#!/usr/bin/env python

"""
TODO: add docs
"""
import os
import traceback
import json
import threading
import time
from fireworks.core.firework import FWAction
from fireworks.core.fw_config import FWConfig

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'


def ping_launch(launchpad, launch_id, stop_event):
    while not stop_event.is_set():
        launchpad._ping_launch(launch_id)
        stop_event.wait(FWConfig().PING_TIME_SECS)


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
        finish_state = 'COMPLETED'  # the default state to finish in, assuming no errors
        all_stored_data = {}  # stored data for *all* the Tasks

        lp = self.launchpad
        launch_dir = os.path.abspath(os.getcwd())

        # check a FW job out of the launchpad
        m_fw, launch_id = lp._checkout_fw(self.fworker, launch_dir, self.fw_id)
        if not m_fw:
            raise ValueError("No FireWorks are ready to run and match query! {}".format(self.fworker.query))

        # write FW.json and/or FW.yaml to the directory
        if FWConfig().PRINT_FW_JSON:
            m_fw.to_file('FW.json')
        if FWConfig().PRINT_FW_YAML:
            m_fw.to_file('FW.yaml')

        # TODO: add checkpoint stuff

        # set up heartbeat (pinging the server that we're still alive)
        ping_stop = threading.Event()
        ping_thread = threading.Thread(target=ping_launch,  args=(lp, launch_id, ping_stop))
        ping_thread.start()

        for my_task in m_fw.tasks:
            try:
                m_action = my_task.run_task(m_fw.spec)

                # read in a FWAction from a file, in case the task is not Python and cannot return it explicitly
                if os.path.exists('FWAction.json'):
                    m_action = FWAction.from_file('FWAction.json')
                elif os.path.exists('FWAction.yaml'):
                    m_action = FWAction.from_file('FWAction.yaml')

                if not m_action:
                    m_action = FWAction('CONTINUE')

                # update the global stored data with the data to store from this particular Task
                all_stored_data.update(m_action.stored_data)

                if m_action.command != 'CONTINUE':
                    break;
            except:
                m_action = FWAction('BREAK', {'_message': 'runtime error during task', '_task': my_task.to_dict(), '_exception': traceback.format_exc()})
                finish_state = 'FIZZLED'

        # perform finishing operation
        ping_stop.set()
        m_action.stored_data = all_stored_data
        lp._complete_launch(launch_id, m_action, finish_state)

