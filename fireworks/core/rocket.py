#!/usr/bin/env python

"""
A Rocket fetches a FireWork from the database, runs the sequence of FireTasks inside, and then completes the Launch
"""
from datetime import datetime
import json
import logging
import multiprocessing
import os
import traceback
import threading
from fireworks.core.firework import FWAction, FireWork
from fireworks.fw_config import FWData, PING_TIME_SECS, REMOVE_USELESS_DIRS, PRINT_FW_JSON, PRINT_FW_YAML, STORE_PACKING_INFO
from fireworks.utilities.dict_mods import apply_mod

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'

def do_ping(launchpad, launch_id):
    if launchpad:
            launchpad.ping_launch(launch_id)
    else:
        with open('FW_ping.json', 'w') as f:
            f.write('{"ping_time": "%s"}' % datetime.utcnow().isoformat())

def ping_launch(launchpad, launch_id, stop_event, master_thread):
    while not stop_event.is_set() and master_thread.isAlive():
        do_ping(launchpad, launch_id)
        stop_event.wait(PING_TIME_SECS)

def start_ping_launch(launchpad, launch_id):
    fd = FWData()
    if fd.MULTIPROCESSING:
        if not launch_id:
            raise ValueError("Multiprocessing cannot be run in offline mode!")
        m = fd.DATASERVER
        m.Running_IDs()[os.getpid()] = launch_id
        return None
    else:
        ping_stop = threading.Event()
        ping_thread = threading.Thread(target=ping_launch,
                                       args=(launchpad, launch_id, ping_stop, threading.currentThread()))
        ping_thread.start()
        return ping_stop

def stop_backgrounds(ping_stop, btask_stops):
    fd = FWData()
    if fd.MULTIPROCESSING:
        m = fd.DATASERVER
        m.Running_IDs()[os.getpid()] = None
    else:
        ping_stop.set()

    for b in btask_stops:
        b.set()


def background_task(btask, spec, stop_event, master_thread):
    num_launched = 0
    while not stop_event.is_set() and master_thread.isAlive():
        for task in btask.tasks:
            task.run_task(spec)
        if btask.sleep_time > 0:
            stop_event.wait(btask.sleep_time)

        num_launched += 1
        if num_launched == btask.num_launches:
            break


def start_background_task(btask, spec):
    ping_stop = threading.Event()
    ping_thread = threading.Thread(target=background_task, args=(btask, spec, ping_stop, threading.currentThread()))
    ping_thread.start()
    return ping_stop


class Rocket():
    """
    The Rocket fetches a workflow step from the FireWorks database and executes it.
    """

    def __init__(self, launchpad, fworker, fw_id):
        """

        :param launchpad: (LaunchPad) A LaunchPad object for interacting with the FW database. If none, reads FireWorks from FW.json and writes to FWAction.json
        :param fworker: (FWorker) A FWorker object describing the computing resource
        :param fw_id: (int) id of a specific FireWork to run (quit if it cannot be found)
        """
        self.launchpad = launchpad
        self.fworker = fworker
        self.fw_id = fw_id

    def run(self):
        """
        Run the rocket (check out a job from the database and execute it)
        """
        all_stored_data = {}  # combined stored data for *all* the Tasks
        all_update_spec = {}  # combined update_spec for *all* the Tasks
        all_mod_spec = []  # combined mod_spec for *all* the Tasks

        lp = self.launchpad
        launch_dir = os.path.abspath(os.getcwd())

        # check a FW job out of the launchpad
        if lp:
            m_fw, launch_id = lp.checkout_fw(self.fworker, launch_dir, self.fw_id)
        else:  # offline mode
            m_fw = FireWork.from_file(os.path.join(os.getcwd(), "FW.json"))

            # set the run start time
            with open('FW_offline.json', 'r+') as f:
                d = json.loads(f.read())
                d['started_on'] = datetime.utcnow().isoformat()
                f.seek(0)
                f.write(json.dumps(d))
                f.truncate()

            launch_id = None  # we don't need this in offline mode...

        if not m_fw:
            print("No FireWorks are ready to run and match query! {}".format(self.fworker.query))
            return False

        if '_launch_dir' in m_fw.spec:
            prev_dir = launch_dir
            os.chdir(m_fw.spec['_launch_dir'])
            launch_dir = os.path.abspath(os.getcwd())

            if lp:
                lp.change_launch_dir(launch_id, launch_dir)

            if not os.listdir(prev_dir) and REMOVE_USELESS_DIRS:
                try:
                    os.rmdir(prev_dir)
                except:
                    pass

        if lp:
            message = 'RUNNING fw_id: {} in directory: {}'.\
                format(m_fw.fw_id, os.getcwd())
            lp.log_message(logging.INFO, message)

        # write FW.json and/or FW.yaml to the directory
        if PRINT_FW_JSON:
            m_fw.to_file('FW.json', indent=4)
        if PRINT_FW_YAML:
            m_fw.to_file('FW.yaml')

        try:
            my_spec = dict(m_fw.spec)  # make a copy of spec, don't override original
            my_spec["_fw_env"] = self.fworker.env

            # set up heartbeat (pinging the server that we're still alive)
            ping_stop = start_ping_launch(lp, launch_id)

            # start background tasks
            btask_stops = []
            if '_background_tasks' in my_spec:
                for bt in my_spec['_background_tasks']:
                    btask_stops.append(start_background_task(bt, m_fw.spec))

            # execute the FireTasks!
            for t in m_fw.tasks:
                lp.log_message(logging.INFO, "Task started: %s." % t.fw_name)
                m_action = t.run_task(my_spec)

                # read in a FWAction from a file, in case the task is not Python and cannot return it explicitly
                if os.path.exists('FWAction.json'):
                    m_action = FWAction.from_file('FWAction.json')
                elif os.path.exists('FWAction.yaml'):
                    m_action = FWAction.from_file('FWAction.yaml')

                if not m_action:
                    m_action = FWAction()

                # update the global stored data with the data to store and update from this particular Task
                all_stored_data.update(m_action.stored_data)
                all_update_spec.update(m_action.update_spec)
                all_mod_spec.extend(m_action.mod_spec)

                # update spec for next task as well
                my_spec.update(m_action.update_spec)
                for mod in m_action.mod_spec:
                    apply_mod(mod, my_spec)
                lp.log_message(logging.INFO, "Task completed: %s " % t.fw_name)
                if m_action.skip_remaining_tasks:
                    break

            # add job packing info if this is needed
            if FWData().MULTIPROCESSING and STORE_PACKING_INFO:
                all_stored_data['multiprocess_name'] = multiprocessing.current_process().name

            # perform finishing operation
            stop_backgrounds(ping_stop, btask_stops)
            for b in btask_stops:
                b.set()
            do_ping(lp, launch_id)  # one last ping, esp if there is a monitor
            # last background monitors
            if '_background_tasks' in my_spec:
                for bt in my_spec['_background_tasks']:
                    if bt.run_on_finish:
                        for task in bt.tasks:
                            task.run_task(m_fw.spec)

            m_action.stored_data = all_stored_data
            m_action.mod_spec = all_mod_spec
            m_action.update_spec = all_update_spec

            if lp:
                lp.complete_launch(launch_id, m_action, 'COMPLETED')
            else:
                with open('FW_offline.json', 'r+') as f:
                    d = json.loads(f.read())
                    d['fwaction'] = m_action.to_dict()
                    d['state'] = 'COMPLETED'
                    d['completed_on'] = datetime.utcnow().isoformat()
                    f.seek(0)
                    f.write(json.dumps(d))
                    f.truncate()

            return True

        except:
            stop_backgrounds(ping_stop, btask_stops)
            do_ping(lp, launch_id)  # one last ping, esp if there is a monitor
            traceback.print_exc()
            try:
                m_action = FWAction(stored_data={'_message': 'runtime error during task', '_task': t.to_dict(),
                                             '_exception': traceback.format_exc()}, exit=True)
            except:
                m_action = FWAction(stored_data={'_message': 'runtime error during task', '_task': None,
                                             '_exception': traceback.format_exc()}, exit=True)
            if lp:
                lp.complete_launch(launch_id, m_action, 'FIZZLED')
            else:
                with open('FW_offline.json', 'r+') as f:
                    d = json.loads(f.read())
                    d['fwaction'] = m_action.to_dict()
                    d['state'] = 'FIZZLED'
                    f.seek(0)
                    f.write(json.dumps(d))
                    f.truncate()

            return True


