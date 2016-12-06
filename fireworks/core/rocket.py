# coding: utf-8

from __future__ import unicode_literals

"""
A Rocket fetches a Firework from the database, runs the sequence of FireTasks inside, and then
completes the Launch
"""

from datetime import datetime
import json
import logging
import multiprocessing
import os
import traceback
import threading
import errno
import distutils.dir_util

from fireworks.core.firework import FWAction, Firework
from fireworks.fw_config import FWData, PING_TIME_SECS, REMOVE_USELESS_DIRS, PRINT_FW_JSON, \
    PRINT_FW_YAML, STORE_PACKING_INFO
from fireworks.utilities.dict_mods import apply_mod
from fireworks.core.launchpad import LockedWorkflowError

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
        fd.Running_IDs[os.getpid()] = launch_id
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
        fd.Running_IDs[os.getpid()] = None
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
    ping_thread = threading.Thread(target=background_task, args=(btask, spec, ping_stop,
                                                                 threading.currentThread()))
    ping_thread.start()
    return ping_stop


class Rocket:
    """
    The Rocket fetches a workflow step from the FireWorks database and executes it.
    """

    def __init__(self, launchpad, fworker, fw_id):
        """
        Args:
        launchpad (LaunchPad): A LaunchPad object for interacting with the FW database.
            If none, reads FireWorks from FW.json and writes to FWAction.json
        fworker (FWorker): A FWorker object describing the computing resource
        fw_id (int): id of a specific Firework to run (quit if it cannot be found)
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
            m_fw = Firework.from_file(os.path.join(os.getcwd(), "FW.json"))

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

        final_state = None

        try:
            if '_launch_dir' in m_fw.spec and lp:
                prev_dir = launch_dir
                launch_dir = os.path.expandvars(m_fw.spec['_launch_dir'])
                if not os.path.abspath(launch_dir):
                    launch_dir = os.path.normpath(os.path.join(os.getcwd(), launch_dir))
                # thread-safe "mkdir -p"
                try:
                    os.makedirs(launch_dir)
                except OSError as exception:
                    if exception.errno != errno.EEXIST:
                        raise
                os.chdir(launch_dir)

                if not os.path.samefile(launch_dir, prev_dir):
                    lp.change_launch_dir(launch_id, launch_dir)

                if not os.listdir(prev_dir) and REMOVE_USELESS_DIRS:
                    try:
                        os.rmdir(prev_dir)
                    except:
                        pass

            if m_fw.spec.get('_recover_launch', None):
                launch_to_recover = lp.get_launch_by_id(m_fw.spec['_recover_launch']['_launch_id'])
                starting_task = launch_to_recover.action.stored_data.get('_exception', {}).get('_failed_task_n', 0)
                recovery = launch_to_recover.action.stored_data['_recovery']
                all_stored_data.update(recovery['_all_stored_data'])
                all_update_spec.update(recovery['_all_update_spec'])
                all_mod_spec.extend(recovery['_all_mod_spec'])
                recover_launch_dir = launch_to_recover.launch_dir
                if lp:
                    lp.log_message(
                        logging.INFO,
                        'Recovering from task number {} in folder {}.'.format(starting_task, recover_launch_dir))
                if m_fw.spec['_recover_launch']['_recover_mode'] == 'cp' and launch_dir != recover_launch_dir:
                    if lp:
                        lp.log_message(
                            logging.INFO,
                            'Copying data from recovery folder {} to folder {}.'.format(recover_launch_dir, launch_dir))
                    distutils.dir_util.copy_tree(recover_launch_dir, launch_dir, update=1)

            else:
                starting_task = 0

            if lp:
                message = 'RUNNING fw_id: {} in directory: {}'.\
                    format(m_fw.fw_id, os.getcwd())
                lp.log_message(logging.INFO, message)

            # write FW.json and/or FW.yaml to the directory
            if PRINT_FW_JSON:
                m_fw.to_file('FW.json', indent=4)
            if PRINT_FW_YAML:
                m_fw.to_file('FW.yaml')

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
            for t_counter, t in enumerate(m_fw.tasks[starting_task:], start=starting_task):
                if lp:
                    lp.log_message(logging.INFO, "Task started: %s." % t.fw_name)

                if my_spec.get("_add_launchpad_and_fw_id"):
                    t.launchpad = self.launchpad
                    t.fw_id = m_fw.fw_id
                if my_spec.get("_add_fworker"):
                    t.fworker = self.fworker

                try:
                    m_action = t.run_task(my_spec)
                except BaseException as e:
                    traceback.print_exc()
                    tb = traceback.format_exc()
                    stop_backgrounds(ping_stop, btask_stops)
                    do_ping(lp, launch_id)  # one last ping, esp if there is a monitor
                    # If the exception is serializable, save its details
                    try:
                        exception_details = e.to_dict()
                    except AttributeError:
                        exception_details = None
                    except BaseException as e:
                        if lp:
                            lp.log_message(logging.WARNING,
                                           "Exception couldn't be serialized: %s " % e)
                        exception_details = None

                    try:
                        m_task = t.to_dict()
                    except:
                        m_task = None

                    m_action = FWAction(stored_data={'_message': 'runtime error during task',
                                                     '_task': m_task,
                                                     '_exception': {'_stacktrace': tb,
                                                                    '_details': exception_details,
                                                                    '_failed_task_n': t_counter},
                                                     '_recovery': {'_all_stored_data': all_stored_data,
                                                                   '_all_update_spec': all_update_spec,
                                                                   '_all_mod_spec': all_mod_spec}},
                                        exit=True)
                    m_action = self.decorate_fwaction(m_action, my_spec, m_fw, launch_dir)

                    if lp:
                        final_state = 'FIZZLED'
                        lp.complete_launch(launch_id, m_action, final_state)
                    else:
                        with open('FW_offline.json', 'r+') as f:
                            d = json.loads(f.read())
                            d['fwaction'] = m_action.to_dict()
                            d['state'] = 'FIZZLED'
                            d['completed_on'] = datetime.utcnow().isoformat()
                            f.seek(0)
                            f.write(json.dumps(d))
                            f.truncate()

                    return True

                # read in a FWAction from a file, in case the task is not Python and cannot return
                # it explicitly
                if os.path.exists('FWAction.json'):
                    m_action = FWAction.from_file('FWAction.json')
                elif os.path.exists('FWAction.yaml'):
                    m_action = FWAction.from_file('FWAction.yaml')

                if not m_action:
                    m_action = FWAction()

                # update the global stored data with the data to store and update from this
                # particular Task
                all_stored_data.update(m_action.stored_data)
                all_update_spec.update(m_action.update_spec)
                all_mod_spec.extend(m_action.mod_spec)

                # update spec for next task as well
                my_spec.update(m_action.update_spec)
                for mod in m_action.mod_spec:
                    apply_mod(mod, my_spec)
                if lp:
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

            m_action = self.decorate_fwaction(m_action, my_spec, m_fw, launch_dir)

            if lp:
                final_state = 'COMPLETED'
                lp.complete_launch(launch_id, m_action, final_state)
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

        except LockedWorkflowError as e:
            lp.log_message(logging.DEBUG, traceback.format_exc())
            lp.log_message(logging.WARNING,
                           "Firework {} reached final state {} but couldn't complete the update of "
                           "the database. Reason: {}\nRefresh the WF to recover the result "
                           "(lpad admin refresh -i {}).".format(
                               self.fw_id, final_state, e, self.fw_id))
            return True

        except:
            # problems while processing the results. high probability of malformed data.
            traceback.print_exc()
            stop_backgrounds(ping_stop, btask_stops)
            # restore initial state to prevent the raise of further exceptions
            if lp:
                lp.restore_backup_data(launch_id, m_fw.fw_id)

            do_ping(lp, launch_id)  # one last ping, esp if there is a monitor
            # the action produced by the task is discarded
            m_action = FWAction(stored_data={'_message': 'runtime error during task', '_task': None,
                                             '_exception': {'_stacktrace': traceback.format_exc(),
                                                            '_details': None}},
                                exit=True)

            try:
                m_action = self.decorate_fwaction(m_action, my_spec, m_fw, launch_dir)
            except:
                traceback.print_exc()

            if lp:
                try:
                    lp.complete_launch(launch_id, m_action, 'FIZZLED')
                except LockedWorkflowError as e:
                    lp.log_message(logging.DEBUG, traceback.format_exc())
                    lp.log_message(logging.WARNING,
                                   "Firework {} fizzled but couldn't complete the update of the database."
                                   " Reason: {}\nRefresh the WF to recover the result "
                                   "(lpad admin refresh -i {}).".format(
                                       self.fw_id, final_state, e, self.fw_id))
                    return True
            else:
                with open('FW_offline.json', 'r+') as f:
                    d = json.loads(f.read())
                    d['fwaction'] = m_action.to_dict()
                    d['state'] = 'FIZZLED'
                    d['completed_on'] = datetime.utcnow().isoformat()
                    f.seek(0)
                    f.write(json.dumps(d))
                    f.truncate()

            return True

    def decorate_fwaction(self, fwaction, my_spec, m_fw, launch_dir):

        if my_spec.get("_pass_job_info"):
            job_info = list(my_spec.get("_job_info", []))
            job_info.append({"fw_id": m_fw.fw_id, "name": m_fw.name, "launch_dir": launch_dir})
            fwaction.mod_spec.append({"_push_all": {"_job_info": job_info}})

        if my_spec.get("_preserve_fworker"):
            fwaction.update_spec['_fworker'] = self.fworker.name

        return fwaction
