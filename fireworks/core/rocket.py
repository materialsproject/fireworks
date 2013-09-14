#!/usr/bin/env python

"""
A Rocket fetches a FireWork from the database, runs the sequence of FireTasks inside, and then completes the Launch
"""
import multiprocessing
import os
import traceback
import threading
from fireworks.core.firework import FWAction
from fireworks.core.fw_config import FWConfig, FWData
from fireworks.utilities.fw_utilities import release_db_lock

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'


def ping_launch(launchpad, launch_id, stop_event, master_thread):
    while not stop_event.is_set() and master_thread.isAlive():
        launchpad.ping_launch(launch_id)
        stop_event.wait(FWConfig().PING_TIME_SECS)


def start_ping_launch(launch_id, lp):
    fd = FWData()
    if fd.MULTIPROCESSING:
        m = fd.DATASERVER
        m.Running_IDs()[os.getpid()] = launch_id
        return None
    else:
        ping_stop = threading.Event()
        ping_thread = threading.Thread(target=ping_launch,
                                       args=(lp, launch_id, ping_stop, threading.currentThread()))
        ping_thread.start()
        return ping_stop

def stop_ping_launch(ping_stop):
    fd = FWData()
    if fd.MULTIPROCESSING:
        m = fd.DATASERVER
        m.Running_IDs()[os.getpid()] = None
    else:
        ping_stop.set()


class Rocket():
    """
    The Rocket fetches a workflow step from the FireWorks database and executes it.
    """

    def __init__(self, launchpad, fworker, fw_id):
        """
        
        :param launchpad: A LaunchPad object for interacting with the FW database
        :param fworker: A FWorker object describing the computing resource
        :param fw_id: id of a specific FireWork to run (quit if it cannot be found)
        """
        self.launchpad = launchpad
        self.fworker = fworker
        self.fw_id = fw_id


    def run(self):
        """
        Run the rocket (check out a job from the database and execute it)
        """
        all_stored_data = {}  # stored data for *all* the Tasks

        lp = self.launchpad
        launch_dir = os.path.abspath(os.getcwd())

        # check a FW job out of the launchpad
        m_fw, launch_id = lp.checkout_fw(self.fworker, launch_dir, self.fw_id)
        release_db_lock()
        if not m_fw:
            raise ValueError("No FireWorks are ready to run and match query! {}".format(self.fworker.query))

        if '_launch_dir' in m_fw.spec:
            prev_dir = launch_dir
            os.chdir(m_fw.spec['_launch_dir'])
            launch_dir = os.path.abspath(os.getcwd())
            lp._change_launch_dir(launch_id, launch_dir)

            if not os.listdir(prev_dir) and FWConfig().REMOVE_USELESS_DIRS:
                try:
                    os.rmdir(prev_dir)
                except:
                    pass

        # write FW.json and/or FW.yaml to the directory
        if FWConfig().PRINT_FW_JSON:
            m_fw.to_file('FW.json', indent=4)
        if FWConfig().PRINT_FW_YAML:
            m_fw.to_file('FW.yaml')

        # set up heartbeat (pinging the server that we're still alive)
        try:
            ping_stop = start_ping_launch(launch_id, lp)

            # execute the FireTasks!
            for my_task in m_fw.tasks:
                m_action = my_task.run_task(m_fw.spec)

                # read in a FWAction from a file, in case the task is not Python and cannot return it explicitly
                if os.path.exists('FWAction.json'):
                    m_action = FWAction.from_file('FWAction.json')
                elif os.path.exists('FWAction.yaml'):
                    m_action = FWAction.from_file('FWAction.yaml')

                if not m_action:
                    m_action = FWAction()

                # update the global stored data with the data to store from this particular Task
                all_stored_data.update(m_action.stored_data)

                if m_action.skip_remaining_tasks:
                    break

            # add job packing info if this is needed
            if FWData().MULTIPROCESSING and FWConfig().STORE_PACKING_INFO:
                all_stored_data['multiprocess_name'] = multiprocessing.current_process().name

            # perform finishing operation
            stop_ping_launch(ping_stop)
            m_action.stored_data = all_stored_data
            lp.complete_launch(launch_id, m_action, 'COMPLETED')

        except:
            stop_ping_launch(ping_stop)
            traceback.print_exc()
            m_action = FWAction(stored_data={'_message': 'runtime error during task', '_task': my_task.to_dict(),
                                             '_exception': traceback.format_exc()}, exit=True)
            lp.complete_launch(launch_id, m_action, 'FIZZLED')

