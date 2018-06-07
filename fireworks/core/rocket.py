# coding: utf-8

from __future__ import unicode_literals

from monty.os.path import zpath

"""
A Rocket fetches a Firework from the database, runs the sequence of Firetasks inside, and then
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
import glob
import shutil
import pdb
import distutils.dir_util
from monty.io import zopen
from monty.serialization import loadfn, dumpfn

from fireworks.core.firework import FWAction, Firework
from fireworks.fw_config import FWData, PING_TIME_SECS, REMOVE_USELESS_DIRS, \
    PRINT_FW_JSON, \
    PRINT_FW_YAML, STORE_PACKING_INFO, ROCKET_STREAM_LOGLEVEL
from fireworks.utilities.dict_mods import apply_mod
from fireworks.core.launchpad import LockedWorkflowError, LaunchPad
from fireworks.utilities.fw_utilities import get_fw_logger

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
    elif ping_stop:
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

    def run(self, pdb_on_exception=False):
        """
        Run the rocket (check out a job from the database and execute it)

        Args:
            pdb_on_exception (bool): whether to invoke the debugger on
                a caught exception.  Default False.
        """
        all_stored_data = {}  # combined stored data for *all* the Tasks
        all_update_spec = {}  # combined update_spec for *all* the Tasks
        all_mod_spec = []  # combined mod_spec for *all* the Tasks

        lp = self.launchpad
        launch_dir = os.path.abspath(os.getcwd())
        logdir = lp.get_logdir() if lp else None
        l_logger = get_fw_logger('rocket.launcher', l_dir=logdir,
                                 stream_level=ROCKET_STREAM_LOGLEVEL)

        # check a FW job out of the launchpad
        if lp:
            m_fw, launch_id = lp.checkout_fw(self.fworker, launch_dir, self.fw_id)
        else:  # offline mode
            m_fw = Firework.from_file(os.path.join(os.getcwd(), "FW.json"))

            # set the run start time
            fpath = zpath("FW_offline.json")
            with zopen(fpath) as f_in:
                d = json.loads(f_in.read())
                d['started_on'] = datetime.utcnow().isoformat()
                with zopen(fpath, "wt") as f_out:
                    f_out.write(json.dumps(d, ensure_ascii=False))

            launch_id = None  # we don't need this in offline mode...

        if not m_fw:
            print("No FireWorks are ready to run and match query! {}".format(self.fworker.query))
            return False

        final_state = None
        ping_stop = None
        btask_stops = []

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

            recovery = m_fw.spec.get('_recovery', None)
            if recovery:
                recovery_dir = recovery.get('_prev_dir')
                recovery_mode = recovery.get('_mode')
                starting_task = recovery.get('_task_n')
                all_stored_data.update(recovery.get('_all_stored_data'))
                all_update_spec.update(recovery.get('_all_update_spec'))
                all_mod_spec.extend(recovery.get('_all_mod_spec'))
                if lp:
                    l_logger.log(
                                logging.INFO,
                                'Recovering from task number {} in folder {}.'.format(starting_task,
                                                                                      recovery_dir))
                if recovery_mode == 'cp' and launch_dir != recovery_dir:
                    if lp:
                        l_logger.log(
                                    logging.INFO,
                                    'Copying data from recovery folder {} to folder {}.'.format(recovery_dir,
                                                                                                launch_dir))
                    distutils.dir_util.copy_tree(recovery_dir, launch_dir, update=1)

            else:
                starting_task = 0
                files_in = m_fw.spec.get("_files_in", {})
                prev_files = m_fw.spec.get("_files_prev", {})
                for f in set(files_in.keys()).intersection(prev_files.keys()):
                    # We use zopen for the file objects for transparent handling
                    # of zipped files. shutil.copyfileobj does the actual copy
                    # in chunks that avoid memory issues.
                    with zopen(prev_files[f], "rb") as fin, zopen(files_in[f], "wb") as fout:
                        shutil.copyfileobj(fin, fout)

            if lp:
                message = 'RUNNING fw_id: {} in directory: {}'.\
                    format(m_fw.fw_id, os.getcwd())
                l_logger.log(logging.INFO, message)

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
            if '_background_tasks' in my_spec:
                for bt in my_spec['_background_tasks']:
                    btask_stops.append(start_background_task(bt, m_fw.spec))

            # execute the Firetasks!
            for t_counter, t in enumerate(m_fw.tasks[starting_task:], start=starting_task):
                checkpoint = {'_task_n': t_counter,
                              '_all_stored_data': all_stored_data,
                              '_all_update_spec': all_update_spec,
                              '_all_mod_spec': all_mod_spec}
                Rocket.update_checkpoint(lp, launch_dir, launch_id, checkpoint)
 
                if lp:
                   l_logger.log(logging.INFO, "Task started: %s." % t.fw_name)

                if my_spec.get("_add_launchpad_and_fw_id"):
                    t.fw_id = m_fw.fw_id
                    if FWData().MULTIPROCESSING:
                        # hack because AutoProxy manager can't access attributes
                        t.launchpad = LaunchPad.from_dict(self.launchpad.to_dict())
                    else:
                        t.launchpad = self.launchpad

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
                    if pdb_on_exception:
                        pdb.post_mortem()
                    try:
                        exception_details = e.to_dict()
                    except AttributeError:
                        exception_details = None
                    except BaseException as e:
                        if lp:
                            l_logger.log(logging.WARNING,
                                        "Exception couldn't be serialized: %s " % e)
                        exception_details = None

                    try:
                        m_task = t.to_dict()
                    except:
                        m_task = None

                    m_action = FWAction(stored_data={'_message': 'runtime error during task',
                                                     '_task': m_task,
                                                     '_exception': {'_stacktrace': tb,
                                                                    '_details': exception_details}},
                                        exit=True)
                    m_action = self.decorate_fwaction(m_action, my_spec, m_fw, launch_dir)

                    if lp:
                        final_state = 'FIZZLED'
                        lp.complete_launch(launch_id, m_action, final_state)
                    else:
                        fpath = zpath("FW_offline.json")
                        with zopen(fpath) as f_in:
                            d = json.loads(f_in.read())
                            d['fwaction'] = m_action.to_dict()
                            d['state'] = 'FIZZLED'
                            d['completed_on'] = datetime.utcnow().isoformat()
                            with zopen(fpath, "wt") as f_out:
                                f_out.write(json.dumps(d, ensure_ascii=False))

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
                    l_logger.log(logging.INFO, "Task completed: %s " % t.fw_name)
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

                fpath = zpath("FW_offline.json")
                with zopen(fpath) as f_in:
                    d = json.loads(f_in.read())
                    d['fwaction'] = m_action.to_dict()
                    d['state'] = 'COMPLETED'
                    d['completed_on'] = datetime.utcnow().isoformat()
                    with zopen(fpath, "wt") as f_out:
                        f_out.write(json.dumps(d, ensure_ascii=False))

            return True

        except LockedWorkflowError as e:
            l_logger.log(logging.DEBUG, traceback.format_exc())
            l_logger.log(logging.WARNING,
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
                    l_logger.log(logging.DEBUG, traceback.format_exc())
                    l_logger.log(logging.WARNING,
                                   "Firework {} fizzled but couldn't complete the update of the database."
                                   " Reason: {}\nRefresh the WF to recover the result "
                                   "(lpad admin refresh -i {}).".format(
                                       self.fw_id, final_state, e, self.fw_id))
                    return True
            else:
                fpath = zpath("FW_offline.json")
                with zopen(fpath) as f_in:
                    d = json.loads(f_in.read())
                    d['fwaction'] = m_action.to_dict()
                    d['state'] = 'FIZZLED'
                    d['completed_on'] = datetime.utcnow().isoformat()
                    with zopen(fpath, "wt") as f_out:
                        f_out.write(json.dumps(d, ensure_ascii=False))

            return True

    @staticmethod
    def update_checkpoint(launchpad, launch_dir, launch_id, checkpoint):
        """
        Helper function to update checkpoint

        Args:
            launchpad (LaunchPad): LaunchPad to ping with checkpoint data
            launch_dir (str): directory in which FW_offline.json was created
            launch_id (int): launch id to update
            checkpoint (dict): checkpoint data
        """
        if launchpad:
            launchpad.ping_launch(launch_id, checkpoint=checkpoint)
        else:
            fpath = zpath("FW_offline.json")
            with zopen(fpath) as f_in:
                d = json.loads(f_in.read())
                d['checkpoint'] = checkpoint
                with zopen(fpath, "wt") as f_out:
                    f_out.write(json.dumps(d, ensure_ascii=False))

    def decorate_fwaction(self, fwaction, my_spec, m_fw, launch_dir):

        if my_spec.get("_pass_job_info"):
            job_info = list(my_spec.get("_job_info", []))
            this_job_info = {"fw_id": m_fw.fw_id, "name": m_fw.name, "launch_dir": launch_dir}
            if this_job_info not in job_info:
                job_info.append(this_job_info)
            fwaction.mod_spec.append({"_push_all": {"_job_info": job_info}})

        if my_spec.get("_preserve_fworker"):
            fwaction.update_spec['_fworker'] = self.fworker.name

        if my_spec.get("_files_out"):
            # One potential area of conflict is if a fw depends on two fws
            # and both fws generate the exact same file. That can lead to
            # overriding. But as far as I know, this is an illogical use
            # of a workflow, so I can't see it happening in normal use.
            filepaths = {}
            for k, v in my_spec.get("_files_out").items():
                files = glob.glob(os.path.join(launch_dir, v))
                if files:
                    filepaths[k] = sorted(files)[-1]
            fwaction.update_spec["_files_prev"] = filepaths
        elif "_files_prev" in my_spec:
            # This ensures that _files_prev are not passed from Firework to
            # Firework. We do not want output files from fw1 to be used by fw3
            # in the sequence of fw1->fw2->fw3
            fwaction.update_spec["_files_prev"] = {}

        return fwaction
