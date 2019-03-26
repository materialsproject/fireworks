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

from typing import List, Tuple, Dict

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

    """THE FOLLOWING ARE BASIC FWSerializable FUNCTIONS"""

    @abstractmethod
    def copy(self):
        pass

    @abstractmethod
    def to_dict(self):
        pass

    @abstractmethod
    def update_spec(self, fw_ids: List[int],
                    spec_document: Dict):
        """
        Update fireworks with a spec. Sometimes you need to modify a firework in progress.

        Args:
            fw_ids [int]: All fw_ids to modify.
            spec_document (dict): The spec document. Note that only modifications to
                the spec key are allowed. So if you supply {"_tasks.1.parameter": "hello"},
                you are effectively modifying spec._tasks.1.parameter in the actual fireworks
                collection.
            mongo (bool): spec_document uses mongo syntax to directly update the spec

        TODO addres mongo variable, shouldn't be needed in general
        """
        pass

    @abstractmethod
    @classmethod
    def from_dict(cls, d: Dict):
        pass

    @classmethod
    def auto_load(cls):
        if LAUNCHPAD_LOC:
            return LaunchPad.from_file(LAUNCHPAD_LOC)
        return LaunchPad()

    """FUNCTIONS ACCESSED BY EXTERNAL CODE (lpad_run.py, rocket.py)"""

    """FUNCTION DEFINED IN FULL HERE"""

    @abstractmethod
    def reset(self, password: str, require_password: bool=True,
              max_reset_wo_password: int=25):
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

    def maintain(self, infinite: bool=True, maintain_interval: Optional[int]=None):
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

    def add_wf(self, wf: Union[Workflow, Firework], reassign_all: bool=True):
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

    def bulk_add_wfs(self, wfs: List[Workflow]):
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

    def append_wf(self, new_wf: Workflow, fw_ids: List[int],
                  detour: bool=False, pull_spec_mods: bool=True):
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

    def get_wf_summary_dict(self, fw_id: int, mode: str="more"):
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

    def pause_fw(self, fw_id: int):
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


    def defuse_fw(self, fw_id: int, rerun_duplicates: bool=True):
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

    def reignite_fw(self, fw_id: int):
        """
        Given the firework id, re-ignite(set state=WAITING) the defused firework.

        Args:
            fw_id (int): firework id
        """
        f = self._refresh_wf(fw_id, state='WAITING', allowed_states='DEFUSED')
        return f

    def resume_fw(self, fw_id: int):
        """
        Given the firework id, resume (set state=WAITING) the paused firework.

        Args:
            fw_id (int): firework id
        """
        f = self._refresh_wf(fw_id, state='WAITING', allowed_states='PAUSED')
        return f

    def rerun_fw(self, fw_id: int, rerun_duplicates: bool=True,
                 recover_launch: Union[str,int,None]=None,
                 recover_mode: Optional[str]=None):
        """
        Rerun the firework corresponding to the given id.

        Args:
            fw_id (int): firework id
            rerun_duplicates (bool): flag for whether duplicates should be rerun
            recover_launch ('last' or int): launch_id for last recovery, if set to
                'last' (default), recovery will find the last available launch.
                If it is an int, will recover that specific launch
            recover_mode ('prev_dir' or 'copy'): flag to indicate whether to copy
                or run recovery fw in previous directory

        Returns:
            [int]: list of firework ids that were rerun
        """
        m_fw = self.fireworks.find_one({"fw_id": fw_id}, {"state": 1})

        if not m_fw:
            raise ValueError("FW with id: {} not found!".format(fw_id))

        # detect FWs that share the same launch. Must do this before rerun
        duplicates = []
        reruns = []
        if rerun_duplicates:
            duplicates = self._find_duplicates(fw_id)

        
        self._recover(fw_id, recover_launch)

        # rerun this FW
        if m_fw['state'] in ['ARCHIVED', 'DEFUSED'] :
            self.m_logger.info("Cannot rerun fw_id: {}: it is {}.".format(fw_id, m_fw['state']))
        elif m_fw['state'] == 'WAITING' and not recover_launch:
            self.m_logger.debug("Skipping rerun fw_id: {}: it is already WAITING.".format(fw_id))
        else:
            with WFLock(self, fw_id):
                wf = self.get_wf_by_fw_id_lzyfw(fw_id)
                updated_ids = wf.rerun_fw(fw_id)
                self._update_wf(wf, updated_ids)
                reruns.append(fw_id)

        # rerun duplicated FWs
        for f in duplicates:
            self.m_logger.info("Also rerunning duplicate fw_id: {}".format(f))
            # False for speed, True shouldn't be needed
            r = self.rerun_fw(f, rerun_duplicates=False, recover_launch=recover_launch,
                              recover_mode=recover_mode)
            reruns.extend(r)

        return reruns

    def defuse_wf(self, fw_id: int, defuse_all_states: bool=True):
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

    def archive_wf(self, fw_id: int):
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

    def pause_wf(self, fw_id: int):
        """
        Pause the workflow containing the given firework id.

        Args:
            fw_id (int): firework id
        """
        wf = self.get_wf_by_fw_id_lzyfw(fw_id)
        for fw in wf.fws:
            if fw.state not in ["COMPLETED", "FIZZLED", "DEFUSED"]:
                self.pause_fw(fw.fw_id)

    def reignite_wf(self, fw_id: int):
        """
         Reignite the workflow containing the given firework id.

         Args:
             fw_id (int): firework id
         """
        wf = self.get_wf_by_fw_id_lzyfw(fw_id)
        for fw in wf.fws:
            self.reignite_fw(fw.fw_id)

    def complete_firework(self, fw_id: int, action: Optional[FWAction]=None,
                          state: str='COMPLETED'):
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

    def checkout_fw(self, fworker: FWorker, launch_dir: str, fw_id: int=None,
                    host: Optional[str]=None, ip: Optional[str]=None,
                    state: str="RUNNING"):
        """
        Checkout the next ready firework, mark it with the given state(RESERVED or RUNNING) and
        return it to the caller. The caller is responsible for running the Firework.

        Args:
            fworker (FWorker): A FWorker instance
            launch_dir (str): the dir the FW will be run in (for creating a Launch object)
            fw_id (int): Firework id
            host (str): the host making the request (for creating a Launch object)
            ip (str): the ip making the request (for creating a Launch object)
            state (str): RESERVED or RUNNING, the fetched firework's state will be set to this value.

        Returns:
            (Firework, int): firework and the new launch id
        """
        m_fw = self._get_a_fw_to_run(fworker.query, fw_id=fw_id)
        if not m_fw:
            return None, None

        # If this Launch was previously reserved, overwrite that reservation with this Launch
        # note that adding a new Launch is problematic from a duplicate run standpoint
        prev_reservations = [l for l in m_fw.launches if l.state == 'RESERVED']
        reserved_launch = None if not prev_reservations else prev_reservations[0]
        state_history = reserved_launch.state_history if reserved_launch else None

        # get new launch
        launch_id = reserved_launch.launch_id if reserved_launch else self.get_new_launch_id()
        trackers = [Tracker.from_dict(f) for f in m_fw.spec['_trackers']] if '_trackers' in m_fw.spec else None
        m_launch = Launch(state, launch_dir, fworker, host, ip, trackers=trackers,
                          state_history=state_history, launch_id=launch_id, fw_id=m_fw.fw_id)

        # insert the launch
        #self.launches.find_one_and_replace({'launch_id': m_launch.launch_id},
        #                                   m_launch.to_db_dict(), upsert=True)

        self.m_logger.debug('Created/updated Launch with launch_id: {}'.format(launch_id))

        # update the firework's launches
        if not reserved_launch:
            # we're appending a new Firework
            m_fw.launches.append(m_launch)
        else:
            # we're updating an existing launch
            m_fw.launches = [m_launch if l.launch_id == m_launch.launch_id else l for l in m_fw.launches]

        # insert the firework and refresh the workflow
        m_fw.state = state
        self._upsert_fws([m_fw])
        self._refresh_wf(m_fw.fw_id, state=state)

        # update any duplicated runs
        if state == "RUNNING":
            #for fw in self.fireworks.find(
            #        {'launches': launch_id,
            #         'state': {'$in': ['WAITING', 'READY', 'RESERVED', 'FIZZLED']}}, {'fw_id': 1}):
            for fw in self._find_fws(1,
                                    allowed_states = ['WAITING', 'READY', 'RESERVED', 'FIZZLED'],
                                    find_one = False):
                fw_id = fw['fw_id']
                fw = self.get_fw_by_id(fw_id)
                fw.state = state
                self._upsert_fws([fw])
                self._refresh_wf(fw.fw_id, state=state)

        # Store backup copies of the initial data for retrieval in case of failure
        self.backup_launch_data[m_launch.launch_id] = m_launch.to_db_dict()
        self.backup_fw_data[fw_id] = m_fw.to_db_dict()

        self.m_logger.debug('{} FW with id: {}'.format(m_fw.state, m_fw.fw_id))

        return m_fw, launch_id

    def ping_firework(self, fw_id: int,
                      ptime: Optional[datetime.datetime]=None,
                      checkpoint: Dict=None):
        """
        Ping that a Launch is still alive: updates the 'update_on 'field of the state history of a
        Launch.

        Args:
            launch_id (int)
            ptime (datetime)
        """
        m_fw = self.get_firework_by_id(fw_id)
        for tracker in m_fw.trackers:
            tracker.track_file(m_fw.launch_dir)
        m_fw.touch_history(ptime, checkpoint=checkpoint)
        self._update_fw(fw_id, m_fw)



    """ EXTERNALLY CALLABLE FUNCTIONS WITH ABSTRACT DECLARATIONS """

    @abstractmethod
    def detect_unreserved(self, expiration_secs=RESERVATION_EXPIRATION_SECS, rerun=False):
        pass

    @abstractmethod
    def detect_lostruns(self, expiration_secs=RUN_EXPIRATION_SECS, fizzle=False, rerun=False,
                        max_runtime=None, min_runtime=None, refresh=False, query=None):
        pass

    @abstractmethod
    def update_spec(self, fw_ids, spec_document, mongo=False):
        pass

    @abstractmethod
    def _refresh_wf(self, fw_id):
        pass

    @abstractmethod
    def set_priority(self, fw_id, priority):
        pass

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
    def get_fw_ids(self, query=None, sort=None, limit=0, count_only=False):
        pass

    @abstractmethod
    def get_wf_ids(self, query=None, sort=None, limit=0, count_only=False):
        pass

    @abstractmethod
    def tuneup(self, bkground=True):
        pass

    # might be able to define functions below here

    @abstractmethod
    def get_tracker_data(self, fw_id):
        pass

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

    """ new external functions to replace member accesses """
    @abstractmethod
    def print_tracker_output(self, fw_id):
        # replaces access to lp.fireworks in lpad_run.py
        pass

    # edit recover_offline to avoid accessing lp.launches and lp.offline_runs
    # add a _reset_warning that optionally gets called at the beginning of the reset
    #   function. This will replace the reset function in lapd_runs.py



    """ INTERNAL FUNCTIONS """

    """ INTERNAL FUNCTIONS FULLY DEFINED HERE """

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



    """ INTERNAL FUNCTION WITH ABSTRACT DECLARATIONS """

    @abstractmethod
    def _reset(self):
        """
        Helper method to reset the database. Should perform
        all backend-specific reset operations.
        """
        pass

    @abstractmethod
    def _update_wf(self, wf, updated_ids):
        pass

    @abstractmethod
    def _update_fw(self, fw_id, m_fw):
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
    def _restart_ids(self, next_fw_id):
        pass

    @abstractmethod
    def _get_a_fw_to_run(self, query=None, fw_id=None, checkout=True):
        pass

    @abstractmethod
    def _get_wf_data(self, wf_id):
        pass

    @abstractmethod
    def _complete_fw(self, fw, action, state):
        pass

    @abstractmethod
    def _find_duplciates(self, fw_id):
        pass

    @abstractmethod
    def _recover(self, fw_id, recover_launch = None):
        pass

    @abstractmethod
    def _find_fws(self, fw_id, allowed_states=None, find_one=False):
        pass



    """ LOGGING AND DIRECTORY UTILITIES """

    def get_logdir(self):
        """
        Return the log directory.
        AJ: This is needed for job packing due to Proxy objects not being fully featured...
        """
        return self.logdir

    def log_message(self, level, message):
        """
        Support for job packing

        Args:
            level (str)
            message (str)
        """
        self.m_logger.log(level, message)

    def get_launchdir(self, fw_id):
        return self.get_fw_by_id(fw_id).launch_dir



    # *** USEFUL (BUT NOT REQUIRED) FUNCTIONS

    def _check_fw_for_uniqueness(self, m_fw):
        raise NotImplementedError

    def _restart_ids(self, next_fw_id, next_launch_id):
        raise NotImplementedError

    def get_fw_dict_by_id(self, fw_id):
        raise NotImplementedError