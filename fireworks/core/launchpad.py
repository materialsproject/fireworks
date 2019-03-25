# coding: utf-8

from __future__ import unicode_literals

from monty.io import zopen
from monty.os.path import zpath

"""
The LaunchPad manages the FireWorks database.
"""

import datetime
import json
import os
import random
import time
import traceback
import shutil
import gridfs
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from itertools import chain
from tqdm import tqdm
from bson import ObjectId

from pymongo import MongoClient
from pymongo import DESCENDING, ASCENDING
from pymongo.errors import DocumentTooLarge
from monty.serialization import loadfn

from fireworks.fw_config import LAUNCHPAD_LOC, SORT_FWS, RESERVATION_EXPIRATION_SECS, \
    RUN_EXPIRATION_SECS, MAINTAIN_INTERVAL, WFLOCK_EXPIRATION_SECS, WFLOCK_EXPIRATION_KILL, \
    MONGO_SOCKET_TIMEOUT_MS, GRIDFS_FALLBACK_COLLECTION
from fireworks.utilities.fw_serializers import FWSerializable, reconstitute_dates
from fireworks.core.firework import Firework, Launch, Workflow, FWAction, Tracker
from fireworks.utilities.fw_utilities import get_fw_logger

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Jan 30, 2013'

# TODO: lots of duplication reduction and cleanup possible

class LaunchPad(FWSerializable, ABC):

    @abstractmethod
    def __init__(*args, **kwargs):
        pass

    @abstractmethod
    def copy(self):
        pass

    @abstractmethod
    def to_dict(self):
        pass

    @abstractmethod
    def update_spec(self, fw_ids, spec_document):
        pass

    @abstractmethod
    @classmethod
    def from_dict(cls, d):
        pass

    @classmethod
    def auto_load(cls):
        if LAUNCHPAD_LOC:
            return LaunchPad.from_file(LAUNCHPAD_LOC)
        return LaunchPad()

    @abstractmethod
    def _reset(self):
        pass

    @abstractmethod
    def reset(self, password, require_password=True, max_reset_wo_password=25):
        """
        Create a new FireWorks database. This will overwrite the existing FireWorks database! To
        safeguard against accidentally erasing an existing database, a password must be entered.

        Args:
            password (str): A String representing today's date, e.g. '2012-12-31'
            require_password (bool): Whether a password is required to reset the DB. Setting to
                false is dangerous because running code unintentionally could clear your DB - use
                max_reset_wo_password to minimize risk.
            max_reset_wo_password (int): A failsafe; when require_password is set to False,
                FWS will not clear DBs that contain more workflows than this parameter
        """
        m_password = datetime.datetime.now().strftime('%Y-%m-%d')

        if password == m_password or (not require_password and self.workflows.count() <= max_reset_wo_password):
            self._reset()
        elif not require_password:
            raise ValueError("Password check cannot be overridden since the size of DB ({} workflows) "
                             "is greater than the max_reset_wo_password parameter ({}).".format(
                self.fireworks.count(), max_reset_wo_password))
        else:
            raise ValueError("Invalid password! Password is today's date: {}".format(m_password))

    @abstractmethod
    def detect_lostruns(self, expiration_secs=RUN_EXPIRATION_SECS, fizzle=False, rerun=False,
                        max_runtime=None, min_runtime=None, refresh=False, query=None):
        pass

    @abstractmethod
    def detect_unreserved(self, expiration_secs=RESERVATION_EXPIRATION_SECS, rerun=False):
        pass

    @abstractmethod
    def update_spec(self, fw_ids, spec_document, mongo=False):
        pass

    def maintain(self, infinite=True, maintain_interval=None):
        """
        Perform launchpad maintenance: detect lost runs and unreserved RESERVE launches.

        Args:
            infinite (bool)
            maintain_interval (seconds): sleep time
        """
        maintain_interval = maintain_interval if maintain_interval else MAINTAIN_INTERVAL

        while True:
            self.m_logger.info('Performing maintenance on Launchpad...')
            self.m_logger.debug('Tracking down FIZZLED jobs...')
            fl, ff, inconsistent_fw_ids = self.detect_lostruns(fizzle=True)
            if fl:
                self.m_logger.info('Detected {} FIZZLED launches: {}'.format(len(fl), fl))
                self.m_logger.info('Detected {} FIZZLED FWs: {}'.format(len(ff), ff))
            if inconsistent_fw_ids:
                self.m_logger.info('Detected {} FIZZLED inconsistent fireworks: {}'.format(len(inconsistent_fw_ids),
                                                                                           inconsistent_fw_ids))

            self.m_logger.debug('Tracking down stuck RESERVED jobs...')
            ur = self.detect_unreserved(rerun=True)
            if ur:
                self.m_logger.info('Unreserved {} RESERVED launches: {}'.format(len(ur), ur))

            self.m_logger.info('LaunchPad was MAINTAINED.')

            if not infinite:
                break

            self.m_logger.debug('Sleeping for {} secs...'.format(maintain_interval))
            time.sleep(maintain_interval)

    @abstractmethod
    def _refresh_wf(self, fw_id):
        # this should be abstracted to do the error catching so that
        # functions like pause_wf etc. don't have to
        pass

    @abstractmethod
    def _update_wf(self, wf, updated_ids):
        pass

    @abstractmethod
    def _insert_wfs(self, wfs):
        pass

    @abstractmethod
    def _insert_fws(self, fws):
        pass

    @abstractmethod
    def _upsert_fws(self, fws):
        pass

    @abstractmethod
    def set_priority(self, fw_id, priority):
        pass

    def add_wf(self, wf, reassign_all=True):
        """
        Add workflow(or firework) to the launchpad. The firework ids will be reassigned.

        Args:
            wf (Workflow/Firework)

        Returns:
            dict: mapping between old and new Firework ids
        """
        if isinstance(wf, Firework):
            wf = Workflow.from_Firework(wf)
        # sets the root FWs as READY
        # prefer to wf.refresh() for speed reasons w/many root FWs
        for fw_id in wf.root_fw_ids:
            wf.id_fw[fw_id].state = 'READY'
            wf.fw_states[fw_id] = 'READY'
        # insert the FireWorks and get back mapping of old to new ids
        old_new = self._upsert_fws(list(wf.id_fw.values()), reassign_all=reassign_all)
        # update the Workflow with the new ids
        wf._reassign_ids(old_new)
        # insert the WFLinks
        self._insert_wfs(wf)
        self.m_logger.info('Added a workflow. id_map: {}'.format(old_new))
        return old_new

    def bulk_add_wfs(self, wfs):
        """
        Adds a list of workflows to the fireworks database
        using insert_many for both the fws and wfs, is
        more efficient than adding them one at a time.

        Args:
            wfs ([Workflow]): list of workflows or fireworks

        Returns:
            None

        """
        # Make all fireworks workflows
        wfs = [Workflow.from_firework(wf) if isinstance(wf, Firework)
               else wf for wf in wfs]

        # Initialize new firework counter, starting from the next fw id
        total_num_fws = sum([len(wf.fws) for wf in wfs])
        new_fw_counter = self.fw_id_assigner.find_one_and_update(
            {}, {'$inc': {'next_fw_id': total_num_fws}})['next_fw_id']
        for wf in tqdm(wfs):
            # Reassign fw_ids and increment the counter
            old_new = dict(zip(
                wf.id_fw.keys(),
                range(new_fw_counter, new_fw_counter + len(wf.fws))))
            for fw in wf.fws:
                fw.fw_id = old_new[fw.fw_id]
            wf._reassign_ids(old_new)
            new_fw_counter += len(wf.fws)

            # Set root fws to READY
            for fw_id in wf.root_fw_ids:
                wf.id_fw[fw_id].state = 'READY'
                wf.fw_states[fw_id] = 'READY'

        # Insert all fws and wfs, do workflows first so fws don't
        # get checked out prematurely
        self._insert_wfs(wfs)
        all_fws = chain.from_iterable(wf.fws for wf in wfs)
        self._insert_fws(all_fws)
        return None

    def _edit_db(self, id, command, find_one, update, replace, ):
        pass

    def append_wf(self, new_wf, fw_ids, detour=False, pull_spec_mods=True):
        """
        Append a new workflow on top of an existing workflow.

        Args:
            new_wf (Workflow): The new workflow to append
            fw_ids ([int]): The parent fw_ids at which to append the workflow
            detour (bool): Whether to connect the new Workflow in a "detour" style, i.e., move
            original children of the parent fw_ids to the new_wf
            pull_spec_mods (bool): Whether the new Workflow should pull the FWActions of the parent
                fw_ids
        """
        wf = self.get_wf_by_fw_id(fw_ids[0])
        updated_ids = wf.append_wf(new_wf, fw_ids, detour=detour, pull_spec_mods=pull_spec_mods)
        with WFLock(self, fw_ids[0]):
            self._update_wf(wf, updated_ids)

    @abstractmethod
    def get_fw_by_id(self, fw_id):
        pass

    @abstractmethod
    def get_wf_by_fw_id(self, fw_id):
        pass

    @abstractmethod
    def get_wf_by_fw_id_lzyfw(self, fw_id):
        pass

    @abstractmethod
    def delete_wf(self, fw_id, delete_launch_dirs=False):
        pass

    @abstractmethod
    def _get_wf_data(self, wf_id):
        pass

    @abstractmethod
    def get_wf_summary_dict(self, fw_id, mode="more"):
        """
        A much faster way to get summary information about a Workflow by querying only for
        needed information.

        Args:
            fw_id (int): A Firework id.
            mode (str): Choose between "more", "less" and "all" in terms of quantity of information.

        Returns:
            dict: information about Workflow.
        """
        wf = self._get_wf_data(self, fw_id)

        # Post process the summary dict so that it "looks" better.
        if mode == "less":
            wf["states_list"] = "-".join([fw["state"][:3] if fw["state"].startswith("R")
                                          else fw["state"][0] for fw in wf["fw"]])
            del wf["nodes"]

        if mode == "more" or mode == "all":
            wf["states"] = OrderedDict()
            wf["launch_dirs"] = OrderedDict()
            for fw in wf["fw"]:
                k = "%s--%d" % (fw["name"], fw["fw_id"])
                wf["states"][k] = fw["state"]
                wf["launch_dirs"][k] = [l["launch_dir"] for l in fw["launches"]]
            del wf["nodes"]

        if mode == "all":
            del wf["fw_states"]
            wf["links"] = {id_name_map[int(k)]: [id_name_map[i] for i in v] for k, v in wf["links"].items()}
            wf["parent_links"] = {id_name_map[int(k)]: [id_name_map[i] for i in v]
                                  for k, v in wf["parent_links"].items()}
        if mode == "reservations":
            wf["states"] = OrderedDict()
            wf["launches"] = OrderedDict()
            for fw in wf["fw"]:
                k = "%s--%d" % (fw["name"], fw["fw_id"])
                wf["states"][k] = fw["state"]
                wf["launches"][k] = fw["launches"]
            del wf["nodes"]

        del wf["_id"]
        del wf["fw"]

        return wf

    @abstractmethod
    def get_fw_ids(self, query=None, sort=None, limit=0, count_only=False):
        pass

    @abstractmethod
    def get_wf_ids(self, query=None, sort=None, limit=0, count_only=False):
        pass

    @abstractmethod
    def tuneup(self, bkground=True):
        pass

    def pause_fw(self,fw_id):
        """
        Given the firework id, pauses the firework and refresh the workflow

        Args:
            fw_id(int): firework id
        """
        allowed_states =  ['WAITING', 'READY', 'RESERVED']
        f = self._refresh_wf(fw_id, state='PAUSED', allowed_states=allowed_states)
        if not f:
            self.m_logger.error('No pausable (WAITING,READY,RESERVED) Firework exists with fw_id: {}'.format(fw_id))
        return f


    def defuse_fw(self, fw_id, rerun_duplicates=True):
        """
        Given the firework id, defuse the firework and refresh the workflow.

        Args:
            fw_id (int): firework id
            rerun_duplicates (bool): if True, duplicate fireworks(ones with the same launch) are
                marked for rerun and then defused.
        """
        allowed_states = ['DEFUSED', 'WAITING', 'READY', 'FIZZLED', 'PAUSED']
        f = self._refresh_wf(fw_id, state='DEFUSED', allowed_states=allowed_states)
        if not f:
            self.rerun_fw(fw_id, rerun_duplicates)
            f = self._refresh_wf(fw_id, state='DEFUSED', allowed_states=allowed_states)
        return f

    def reignite_fw(self, fw_id):
        """
        Given the firework id, re-ignite(set state=WAITING) the defused firework.

        Args:
            fw_id (int): firework id
        """
        f = self._refresh_wf(fw_id, state='WAITING', allowed_states='DEFUSED')
        return f

    def resume_fw(self, fw_id):
        """
        Given the firework id, resume (set state=WAITING) the paused firework.

        Args:
            fw_id (int): firework id
        """
        f = self._refresh_wf(fw_id, state='WAITING', allowed_states='PAUSED')
        return f

    @abstractmethod
    def rerun_fw(self, fw_id, rerun_duplicates=True, recover_launch=None, recover_mode=None):
        pass

    def defuse_wf(self, fw_id, defuse_all_states=True):
        """
        Defuse the workflow containing the given firework id.

        Args:
            fw_id (int): firework id
            defuse_all_states (bool)
        """
        wf = self.get_wf_by_fw_id_lzyfw(fw_id)
        for fw in wf.fws:
            if fw.state not in ["COMPLETED", "FIZZLED"] or defuse_all_states:
                self.defuse_fw(fw.fw_id)

    def archive_wf(self, fw_id):
        """
         Archive the workflow containing the given firework id.

         Args:
             fw_id (int): firework id
         """
        # first archive all the launches, so they are not used in duplicate checks
        wf = self.get_wf_by_fw_id_lzyfw(fw_id)
        if wf.state != 'ARCHIVED':
            fw_ids = [f.fw_id for f in wf.fws]
            for fw_id in fw_ids:
                self.rerun_fw(fw_id)

            # second set the state of all FWs to ARCHIVED
            wf = self.get_wf_by_fw_id_lzyfw(fw_id)
            for fw in wf.fws:
                self._refresh_wf(fw_id, state='ARCHIVED')

    def pause_wf(self, fw_id):
        """
        Pause the workflow containing the given firework id.

        Args:
            fw_id (int): firework id
        """
        wf = self.get_wf_by_fw_id_lzyfw(fw_id)
        for fw in wf.fws:
            if fw.state not in ["COMPLETED", "FIZZLED", "DEFUSED"]:
                self.pause_fw(fw.fw_id)

    def reignite_wf(self, fw_id):
        """
         Reignite the workflow containing the given firework id.

         Args:
             fw_id (int): firework id
         """
        wf = self.get_wf_by_fw_id_lzyfw(fw_id)
        for fw in wf.fws:
            self.reignite_fw(fw.fw_id)   

    def run_exists(self, fworker=None):
        """
        Checks to see if the database contains any FireWorks that are ready to run.

        Returns:
            bool: True if the database contains any FireWorks that are ready to run.
        """
        q = fworker.query if fworker else {}
        return bool(self._get_a_fw_to_run(query=q, checkout=False))

    def future_run_exists(self, fworker=None):
        """Check if database has any current OR future Fireworks available

        Returns:
            bool: True if database has any ready or waiting Fireworks.
        """
        if self.run_exists(fworker):
            # check first to see if any are READY
            return True
        else:
            # retrieve all [RUNNING/RESERVED] fireworks
            q = fworker.query if fworker else {}
            q.update({'state': {'$in': ['RUNNING', 'RESERVED']}})
            active = self.get_fw_ids(q)
            # then check if they have WAITING children
            for fw_id in active:
                children = self.get_wf_by_fw_id_lzyfw(fw_id).links[fw_id]
                if any(self.get_fw_dict_by_id(i)['state'] == 'WAITING'
                       for i in children):
                    return True

            # if we loop over all active and none have WAITING children
            # there is no future work to do
            return False

    @abstractmethod
    def _restart_ids(self, next_fw_id):
        pass

    @abstractmethod
    def _get_a_fw_to_run(self, query=None, fw_id=None, checkout=True):
        pass

    def complete_firework(self, fw_id, action=None, state='COMPLETED'):
        """
        Internal method used to mark a Firework's Launch as completed.

        Args:
            launch_id (int)
            action (FWAction): the FWAction of what to do next
            state (str): COMPLETED or FIZZLED

        Returns:
            dict: updated launch
        """
        # update the launch data to COMPLETED, set end time, etc
        m_fw = self.get_fw_by_id(fw_id)
        m_fw.state = state
        if action:
            m_fw.action = action
        self._complete_fw(m_fw, action, state)

        # change return type to dict to make return type serializable to support job packing
        return m_fw.to_dict()

    @abstractmethod
    def checkout_fw(self, fworker, launch_dir, fw_id=None, host=None, ip=None, state="RUNNING"):
        pass

    def reserve_fw(self, fworker, launch_dir, host=None, ip=None, fw_id=None):
        """
        Checkout the next ready firework and mark the launch reserved.

        Args:
            fworker (FWorker)
            launch_dir (str): path to the launch directory.
            host (str): hostname
            ip (str): ip address
            fw_id (int): fw_id to be reserved, if desired

        Returns:
            (Firework, int): the checked out firework and the new launch id
        """
        return self.checkout_fw(fworker, launch_dir, host=host, ip=ip, fw_id=fw_id, state="RESERVED")

    #......

    def mark_fizzled(self, fw_id):
        """
        Mark the launch corresponding to the given id as FIZZLED.

        Args:
            launch_id (int): launch id

        Returns:
            dict: updated launch
        """
        # Do a confirmed write and make sure state_history is preserved
        self.complete_launch(fw_id, state='FIZZLED')

    #......

    def log_message(self, level, message):
        """
        Support for job packing

        Args:
            level (str)
            message (str)
        """
        self.m_logger.log(level, message)

    @abstractmethod
    def get_tracker_data(self, fw_id):
        pass

    def get_launchdir(self, fw_id):
        return self.get_fw_by_id(fw_id).launch_dir

    @abstractmethod
    def change_launch_dir(self, launch_id, launch_dir):
        pass

    @abstractmethod
    def restore_backup_data(self, launch_id, fw_id):
        pass

    @abstractmethod
    def get_reservation_id_from_fw_id(self, fw_id):
        pass

    #can probably make one of these not abstract by moving the error catching around
    @abstractmethod
    def cancel_reservation_by_reservation_id(self, reservation_id):
        pass

    @abstractmethod
    def cancel_reservation(self, launch_id):
        pass

    @abstractmethod
    def add_offline_run(self, launch_id, fw_id, name):
        pass

    @abstractmethod
    def recover_offline(self, launch_id, ignore_errors=False, print_errors=False):
        pass

    @abstractmethod
    def forget_offline(self, launchid_or_fwid, launch_mode=True):
        pass

    @abstractmethod
    def ping_launch(self, launch_id, ptime=None, checkpoint=None):
        pass

    @abstractmethod
    def complete_launch(self, launch_id, action=None, state='COMPLETED'):
        pass

    def get_logdir(self):
        """
        Return the log directory.
        AJ: This is needed for job packing due to Proxy objects not being fully featured...
        """
        return self.logdir

    # *** USEFUL (BUT NOT REQUIRED) FUNCTIONS

    def _check_fw_for_uniqueness(self, m_fw):
        raise NotImplementedError

    def _restart_ids(self, next_fw_id, next_launch_id):
        raise NotImplementedError

    def _get_a_fw_to_run(self, query=None, fw_id=None, checkout=True):
        raise NotImplementedError