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
from fireworks.core.firework import Firework, Tracker, Workflow,\
                                Firetask, FWAction
from fireworks.core.fworker import FWorker
from fireworks.utilities.fw_utilities import get_fw_logger

from typing import List, Tuple, Dict, Union, Optional, Any

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Jan 30, 2013'

# TODO: lots of duplication reduction and cleanup possible

class LockedWorkflowError(ValueError):
    """
    Error raised if the context manager WFLock can't acquire the lock on the WF within the selected
    time interval (WFLOCK_EXPIRATION_SECS), if the killing of the lock is disabled (WFLOCK_EXPIRATION_KILL)
    """
    pass

class WFLock(object):
    """
    Lock a Workflow, i.e. for performing update operations
    Raises a LockedWorkflowError if the lock couldn't be acquired withing expire_secs and kill==False.
    Calling functions are responsible for handling the error in order to avoid database inconsistencies.
    """

    def __init__(self, lp, fw_id, expire_secs=WFLOCK_EXPIRATION_SECS, kill=WFLOCK_EXPIRATION_KILL):
        """
        Args:
            lp (LaunchPad)
            fw_id (int): Firework id
            expire_secs (int): max waiting time in seconds.
            kill (bool): force lock acquisition or not
        """
        self.lp = lp
        self.fw_id = fw_id
        self.expire_secs = expire_secs
        self.kill = kill

    def __enter__(self):
        ctr = 0
        waiting_time = 0
        # acquire lock
        links_dict = self.lp.workflows.find_one_and_update({'nodes': self.fw_id,
                                                            'locked': {"$exists": False}},
                                                           {'$set': {'locked': True}})
        # could not acquire lock b/c WF is already locked for writing
        while not links_dict:
            ctr += 1
            time_incr = ctr/10.0+random.random()/100.0
            time.sleep(time_incr)  # wait a bit for lock to free up
            waiting_time += time_incr
            if waiting_time > self.expire_secs:  # too much time waiting, expire lock
                wf = self.lp.workflows.find_one({'nodes': self.fw_id})
                if not wf:
                    raise ValueError("Could not find workflow in database: {}".format(self.fw_id))
                if self.kill:  # force lock acquisition
                    self.lp.m_logger.warning('FORCIBLY ACQUIRING LOCK, WF: {}'.format(self.fw_id))
                    links_dict = self.lp.workflows.find_one_and_update({'nodes': self.fw_id},
                                                                       {'$set': {'locked': True}})
                else:  # throw error if we don't want to force lock acquisition
                    raise LockedWorkflowError("Could not get workflow - LOCKED: {}".format(self.fw_id))
            else:
                # retry lock
                links_dict = self.lp.workflows.find_one_and_update(
                    {'nodes': self.fw_id, 'locked': {"$exists": False}}, {'$set': {'locked': True}})

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lp.workflows.find_one_and_update({"nodes": self.fw_id}, {"$unset": {"locked": True}})

class LaunchPad(FWSerializable, ABC):

    @abstractmethod
    def __init__(*args, **kwargs):
        pass

    """THE FOLLOWING ARE BASIC FWSerializable FUNCTIONS"""

    @abstractmethod
    def to_dict(self):
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, d: Dict):
        pass

    @classmethod
    def auto_load(cls):
        if LAUNCHPAD_LOC:
            return cls.from_file(LAUNCHPAD_LOC)
        return cls()

###################################################################
# FUNCTIONS ACCESSED BY EXTERNAL CODE (lpad_run.py, rocket.py) #
################################################################
    
#-------------------------------#
# FUNCTION DEFINED IN FULL HERE #
#-------------------------------#

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

        if password == m_password or (not require_password\
                and self.workflows.count() <= max_reset_wo_password):
            self._reset()
        elif not require_password:
            raise ValueError("Password check cannot be overridden since the size of DB ({} workflows) "
                             "is greater than the max_reset_wo_password parameter ({}).".format(
                self.firework_count, max_reset_wo_password))
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
            # TODO REMOVED fl RETURN VARIABLE (LAUNCHES)
            ff, inconsistent_fw_ids = self.detect_lostruns(fizzle=True)
            if ff:
                self.m_logger.info('Detected {} FIZZLED FWs: {}'.format(len(ff), ff))
            if inconsistent_fw_ids:
                self.m_logger.info('Detected {} FIZZLED inconsistent fireworks: {}'.format(len(inconsistent_fw_ids),
                                                                                           inconsistent_fw_ids))

            # TODO SWITCHED BELOW FROM LAUNCHES TO FIREWORKS
            self.m_logger.debug('Tracking down stuck RESERVED jobs...')
            ur = self.detect_unreserved(rerun=True)
            if ur:
                self.m_logger.info('Unreserved {} RESERVED FWs: {}'.format(len(ur), ur))

            self.m_logger.info('LaunchPad was MAINTAINED.')

            if not infinite:
                break

            self.m_logger.debug('Sleeping for {} secs...'.format(maintain_interval))
            time.sleep(maintain_interval)

    def add_wf(self, wf: Union[Workflow, Firework], reassign_all: bool=True) -> Dict:
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
        new_fw_counter = self.get_new_fw_id(total_num_fws)
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

    def get_wf_summary_dict(self, fw_id: int, mode: str="more") -> Dict:
        """
        A much faster way to get summary information about a Workflow by querying only for
        needed information.

        Args:
            fw_id (int): A Firework id.
            mode (str): Choose between "more", "less" and "all" in terms of quantity of information.

        Returns:
            dict: information about Workflow.
        """
        wf = self._get_wf_data(fw_id, mode)

        # Post process the summary dict so that it "looks" better.
        if mode == "less":
            wf["states_list"] = "-".join([fw["state"][:3] if fw["state"].startswith("R")
                                          else fw["state"][0] for fw in wf["fw"]])
            del wf["nodes"]

        print("Getting summary dict")
        if mode == "more" or mode == "all":
            wf["states"] = OrderedDict()
            wf["launch_dir"] = OrderedDict()
            for fw in wf["fw"]:
                k = "%s--%d" % (fw["name"], fw["fw_id"])
                wf["states"][k] = fw["state"]
                # TODO EDITED launch_dirs -> launch_dir, l -> fw
                wf["launch_dir"][k] = fw.get("launch_dir", None)
            del wf["nodes"]

        if mode == "all":
            del wf["fw_states"]
            wf["links"] = {id_name_map[int(k)]: [id_name_map[i] for i in v] for k, v in wf["links"].items()}
            wf["parent_links"] = {id_name_map[int(k)]: [id_name_map[i] for i in v]
                                  for k, v in wf["parent_links"].items()}
        if mode == "reservations":
            wf["states"] = OrderedDict()
            # TODO REMOVED REFERENCE TO LAUNCH HERE
            for fw in wf["fw"]:
                k = "%s--%d" % (fw["name"], fw["fw_id"])
                wf["states"][k] = fw["state"]
                # TODO REMOVED REFERENCE TO LAUNCH HERE
            del wf["nodes"]

        del wf["_id"]
        del wf["fw"]

        return wf

    def pause_fw(self, fw_id: int) -> Dict:
        """
        Given the firework id, pauses the firework and refresh the workflow

        Args:
            fw_id(int): firework id
        """
        allowed_states =  ['WAITING', 'READY', 'RESERVED']
        f = self._update_fw(fw_id, state='PAUSED', allowed_states=allowed_states)
        if f:
            self._refresh_wf(fw_id)
        else:
            self.m_logger.error('No pausable (WAITING,READY,RESERVED) Firework exists with fw_id: {}'.format(fw_id))
        return f.to_db_dict() if f else None


    def defuse_fw(self, fw_id: int, rerun_duplicates: bool=True) -> Dict:
        """
        Given the firework id, defuse the firework and refresh the workflow.

        Args:
            fw_id (int): firework id
            rerun_duplicates (bool): if True, duplicate fireworks(ones with the same launch) are
                marked for rerun and then defused.
        """
        allowed_states = ['DEFUSED', 'WAITING', 'READY', 'FIZZLED', 'PAUSED']
        f = self._update_fw(fw_id, state='DEFUSED', allowed_states=allowed_states)
        if f:
            self._refresh_wf(fw_id)
        else:
            self.rerun_fw(fw_id, rerun_duplicates=rerun_duplicates)
            f = self._update_fw(fw_id, state='DEFUSED', allowed_states=allowed_states)
            if f:
                self._refresh_wf(fw_id)
        return f.to_db_dict() if f else None

    def reignite_fw(self, fw_id: int) -> Dict:
        """
        Given the firework id, re-ignite(set state=WAITING) the defused firework.

        Args:
            fw_id (int): firework id
        """
        f = self._update_fw(fw_id, state='WAITING', allowed_states='DEFUSED')
        self._refresh_wf(fw_id)
        return f.to_db_dict() if f else None

    def resume_fw(self, fw_id: int) -> Dict:
        """
        Given the firework id, resume (set state=WAITING) the paused firework.

        Args:
            fw_id (int): firework id
        """
        f = self._update_fw(fw_id, state='WAITING', allowed_states='PAUSED')
        self._refresh_wf(fw_id)
        return f.to_db_dict() if f else None

    def rerun_fw(self, fw_id: int, launch_idx: int=None, rerun_duplicates: bool=True,
                 recover_mode: Optional[str]=None) -> List[int]:
        # TODO REMOVED recover_launch ARGUMENT FROM THIS FUNCTION

        """
        Rerun the firework corresponding to the given id.

        Args:
            fw_id (int): firework id
            rerun_duplicates (bool): flag for whether duplicates should be rerun
            recover_mode ('prev_dir' or 'copy'): flag to indicate whether to copy
                or run recovery fw in previous directory

        Returns:
            [int]: list of firework ids that were rerun
        """
        m_fw = self.get_fw_dict_by_id(fw_id, launch_idx)

        if not m_fw:
            raise ValueError("FW with id: {} not found!".format(fw_id))

        # TODO CHANGED THIS TO GENERAL DUPLICATE FINDER. USED TO SAY:
        # detect FWs that share the same launch. Must do this before rerun
        duplicates = []
        reruns = []
        if rerun_duplicates:
            duplicates = self._get_duplicates(fw_id)

        self._recover(fw_id, launch_idx, recover_mode)

        # rerun this FW
        if m_fw['state'] in ['ARCHIVED', 'DEFUSED'] :
            self.m_logger.info("Cannot rerun fw_id: {}: it is {}.".format(fw_id, m_fw['state']))
        elif m_fw['state'] == 'WAITING':
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
            r = self.rerun_fw(f, rerun_duplicates=False, recover_mode=recover_mode)
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
        # TODO REMOVED LAUNCH-ARCHIVING STEP
        wf = self.get_wf_by_fw_id_lzyfw(fw_id)
        if wf.state != 'ARCHIVED':
            fw_ids = [f.fw_id for f in wf.fws]
            for fw_id in fw_ids:
                self.rerun_fw(fw_id)

            # second set the state of all FWs to ARCHIVED
            wf = self.get_wf_by_fw_id_lzyfw(fw_id)
            for fw in wf.fws:
                self._update_fw(fw, state='ARCHIVED')
                self._refresh_wf(fw.fw_id)

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

    def delete_wf(self, fw_id: int, delete_launch_dirs: bool=False):
        """
        Delete the workflow containing firework with the given id.

        Args:
            fw_id (int): Firework id
            delete_launch_dirs (bool): if True all the launch directories associated with
                the WF will be deleted as well, if possible.
        """
        links_dict = self._find_wf(fw_id)
        fw_ids = links_dict["nodes"]
        potential_launch_ids = []
        # REMOVED ALL THE LAUNCH-RELATED STUFF HERE, REDUCING TO FIREWORKS
        # SIGNIFICANTLY SIMPLIFIES THIS FUNCTION.

        print("Remove fws %s" % fw_ids)
        print("Removing workflow.")
        launch_dirs = self._delete_wf(fw_id, fw_ids)

        if delete_launch_dirs:
            print("Remove folders %s" % launch_dirs)
            for d in launch_dirs:
                shutil.rmtree(d, ignore_errors=True)

    def checkin_fw(self, fw_id: int,
                   action: Optional[FWAction]=None,
                   state: str='COMPLETED', launch_idx: int=-1) -> Dict:
        # TODO CHANGED launch => firework

        """
        Mark a Firework as completed.

        Args:
            fw_id (int)
            action (FWAction): the FWAction of what to do next
            state (str): COMPLETED or FIZZLED

        Returns:
            dict: updated firework
        """
        # update the FW data to COMPLETED, set end time, etc
        if state == 'FIZZLED':
            print("FW FIZZLED!!!")
            import traceback
            print(traceback.format_exc())

        m_fw = self.get_fw_by_id(fw_id, launch_idx)
        print("CHECKIN STEP", m_fw.state, m_fw.launch_idx, launch_idx)
        self._update_fw(m_fw, state=state)
        if action:
            m_fw.action = action
        m_launch, fw_ids = self._checkin_fw(m_fw, action, state)

        print("CHECKIN STPE", m_launch['state'], m_launch.get('launch_idx'))

        for fw_id in fw_ids:
            self._refresh_wf(fw_id)

        # change return type to dict to make return type serializable to support job packing
        return m_fw.to_dict()

    def checkout_fw(self, fworker: FWorker, launch_dir: str, fw_id: int=None,
                    host: Optional[str]=None, ip: Optional[str]=None,
                    state: str="RUNNING") -> Tuple[Firework, int]:
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
            (Firework, int): firework and the new FW id (TODO PERVIOUSLY launchd id)
        """
        print("FWORKER QUERY", fworker.query)
        m_fw = self._get_a_fw_to_run(fworker.query, fw_id=fw_id)
        if not m_fw:
            return None

        # If this Launch was previously reserved, overwrite that reservation with this Launch
        # note that adding a new Launch is problematic from a duplicate run standpoint
        # TODO REPLACED LAUNCHES WITH FIREWORKS HERE

        prev_reservations = self._find_fws(fw_id=m_fw.fw_id, allowed_states='RESERVED')
        reserved_fw = None if not prev_reservations else Firework.from_dict(prev_reservations[0])
        state_history = reserved_fw.state_history if reserved_fw else []
        trackers = [Tracker.from_dict(f) for f in m_fw.spec['_trackers']] if '_trackers' in m_fw.spec else None

        # get new launch
        # TODO REMOVED LAUNCH ACCESS STUFF BELOW
        # this function should set the arguments in the Firework
        m_fw.reset_launch(state, launch_dir, trackers, state_history, fworker, host, ip,
                          self._get_next_launch_idx(m_fw.fw_id))
        #self._launch_fw(m_fw, reserved_fw)

        self.m_logger.debug('Created/updated Firework with fw_id: {}'.format(m_fw.fw_id))
        # TODO END REMOVED LAUNCH ACCESS

        # insert the firework and refresh the workflow
        m_fw.state = state
        m_fw.set_launch_dir(launch_dir)
        self._upsert_fws([m_fw])
        self._refresh_wf(m_fw.fw_id)

        # update any duplicated runs
        # TODO CHANGED THIS TO USE _find_fws HELPER FUNCTION (ALSO DON'T BACKUP LAUNCH DATA)
        if state == "RUNNING":
            for fw in self._get_duplicates(fw_id, include_self=False,
                    allowed_states=['WAITING', 'READY', 'RESERVED', 'FIZZLED']):
                fw_id = fw['fw_id']
                fw = self.get_fw_by_id(fw_id)
                fw.state = state
                self._upsert_fws([fw])
                self._refresh_wf(fw.fw_id)

        # Store backup copies of the initial data for retrieval in case of failure
        self.backup_fw_data[fw_id] = m_fw.to_db_dict()

        self.m_logger.debug('{} FW with id: {}'.format(m_fw.state, m_fw.fw_id))

        # RETURN fw_id instead of launch_id
        return m_fw

    def ping_firework(self, fw_id: int, launch_idx: int=-1,
                      ptime: Optional[datetime.datetime]=None,
                      checkpoint: Dict=None):
        # TODO REPLACED LAUNCH WITH FIREWORK IN THIS FUNCTION
        """
        Ping that a Launch is still alive: updates the 'update_on 'field of the state history of a
        Launch.

        Args:
            fw_id (int)
            ptime (datetime)
        """
        m_fw = self.get_fw_by_id(fw_id, launch_idx)
        for tracker in m_fw.trackers:
            tracker.track_file(m_fw.launch_dir)
        m_fw.touch_history(ptime, checkpoint=checkpoint)
        self._update_fw(m_fw, touch_history=False)

    def get_tracker_data(self, fw_id: int, launch_idx=-1) -> List[Dict]:
        """
        Args:
            fw_id (id): firework id

        Returns:
            [dict]: list tracker dicts
        """
        data = []
        for fw in self._find_fws(fw_id):
            if 'trackers' in fw:
                trackers = [Tracker.from_dict(t) for t in fw['trackers']]
                data.append({'fw_id': fw['fw_id'], 'launch_idx': fw['launch_dx'],
                            'trackers': trackers})
        return data

    def detect_unreserved(self, expiration_secs: int=RESERVATION_EXPIRATION_SECS,
                          rerun: bool=False) -> List[int]:
        """
        Return the reserved fw ids that have not been updated for a while.

        Args:
            expiration_secs (seconds): time limit
            rerun (bool): if True, the expired reservations are cancelled and the fireworks rerun.

        Returns:
            [int]: list of expired launch ids
        """
        # MOVED INITIAL QUERY FOR BAD RUNS TO A HELPER FUNCTION
        bad_launch_data = [fw_id for fw_id in self._find_timeout_fws('RESERVED', expiration_secs)]
        # not sure if can just remove what was here
        rerun_ids = []
        if rerun:
            for fw_id in bad_launch_data:
                self.cancel_reservation(fw_id)
                if fw_id not in rerun_ids:
                    self.rerun_fw(fw_id)
                    rerun_ids.append(fw_id)
        return bad_launch_data

    def detect_lostruns(self, expiration_secs: int=RUN_EXPIRATION_SECS, fizzle: bool=False,
                        rerun: bool=False, max_runtime: Optional[int]=None,
                        min_runtime: Optional[int]=None, refresh: bool=False,
                        query: Any=None) -> Tuple[List[int], List[int], List[int]]:
        """
        Detect lost runs i.e running fireworks that haven't been updated within the specified
        time limit or running firework that has been marked fizzled or completed.

        Args:
            expiration_secs (seconds): expiration time in seconds
            fizzle (bool): if True, mark the lost runs fizzed
            rerun (bool): if True, mark the lost runs fizzed and rerun
            max_runtime (seconds): maximum run time
            min_runtime (seconds): minimum run time
            refresh (bool): if True, refresh the workflow with inconsistent fireworks.
            query (dict): restrict search to FWs matching this query

        Returns:
            ([int], [int], [int]): tuple of list of lost fw ids, lost firework ids and
                inconsistent firework ids.
        """
        lost_fw_ids = []
        potential_lost_fw_ids = []

        # MOVED INITIAL QUERY FOR BAD RUNS TO A HELPER FUNCTION
        # get a list of FIREWORKS that went bad
        bad_fw_data = self._find_timeout_fws('RUNNING', expiration_secs)

        potential_lost_fw_ids = set()
        lost_fw_ids = []
        lost_launch_idxs = {}
        
        # Check if each FIREWORK is bad. If so, append id to potential_lost_fw_ids
        # and fw_id is ONLY LOST if all its launch_idxs are lost
        for fw_id in bad_fw_data:
            bad_fw = True
            m_fw = self.get_fw_by_id(fw_id)
            if max_runtime or min_runtime:
                bad_fw = False
                utime = m_fw._get_time('RUNNING', use_update_time=True)
                ctime = m_fw._get_time('RUNNING', use_update_time=False)
                if (not max_runtime or (utime-ctime).seconds <= max_runtime) and \
                        (not min_runtime or (utime-ctime).seconds >= min_runtime):
                    bad_fw = True
            if bad_fw:
                potential_lost_fw_ids.add(fw_id)
                if not lost_launch_idxs.get(fw_id):
                    lost_launch_idxs[fw_id] = [m_fw.launch_idx]
                else:
                    lost_launch_idxs[fw_id].append(m_fw.launch_idx)

        # Check if EVERY FIREWORK with a given fw_id failed. If so, add to lost_fw_ids
        for fw_id in potential_lost_fw_ids:  # tricky: figure out what's actually lost
            fws = self._find_fws(fw_id)
            # only RUNNING FireWorks can be "lost", i.e. not defused or archived
            not_lost = [f['launch']['launch_idx'] for f in fws if f['launch']['launch_idx'] not in lost_launch_idxs[fw_id]]
            if len(not_lost) == 0:  # all launches are lost - we are lost!
                lost_fw_ids.append(fw_id)
            else:
                for l_idx in not_lost:
                    l_state = self.get_fw_dict_by_id(fw_id, launch_idx=l_idx)['state']
                    if Firework.STATE_RANKS[l_state] > Firework.STATE_RANKS['FIZZLED']:
                        break
                else:
                    lost_fw_ids.append(fw_id)  # all Launches not lost are anyway FIZZLED / ARCHIVED

        # fizzle and rerun
        if fizzle or rerun:
            for fw_id in lost_fw_ids:
                for launch_idx in lost_launch_idxs[fw_id]:
                    self.mark_fizzled(fw_id, launch_idx)
                if rerun:
                    self.rerun_fw(fw_id)

        # return the lost_launch_idxs (i.e. the lost fireworks)
        # return the lost_fw_ids (i.e. runs that failed for EVERY launch)
        return lost_launch_idxs, lost_fw_ids

    def get_fw_ids_from_reservation_id(self, reservation_id: int):
        """
        Given the reservation id, return the list of firework ids.

        Args:
            reservation_id (int)

        Returns:
            [int]: list of firework ids.
        """
        fws = self._get_fw_ids_from_reservation_id(reservation_id)
        # TODO AVOIDED DUPLICATES
        return list(set([fw['fw_id'] for fw in fws]))

    def cancel_reservation_by_reservation_id(self, reservation_id: int):
        """
        Given the reservation id, cancel the reservation and rerun the corresponding fireworks.
        """
        fw = self._get_fw_ids_from_reservation_id(reservation_id)[0]
        
        if fw:
            self.cancel_reservation(fw['fw_id'])
        else:
            self.m_logger.info("Can't find any reserved jobs with reservation id: {}".format(reservation_id))


    def get_reservation_id_from_fw_id(self, fw_id: int):
        """
        Given the firework id, return the reservation id
        """
        # Should this require launch_idx?
        fws = self._find_fws(fw_id)
        for fw in fws:
            for d in fw['state_history']:
                if 'reservation_id' in d:
                    return d['reservation_id']

    def cancel_reservation(self, fw_id: int):
        """#
        given the launch id, cancel the reservation and rerun the fireworks
        """
        # Should this require launch_idx? I think not because only most recent
        # launch should be reserved. But maybe it's safer since this is called
        # by cancel_reservation_by_reservation_id
        # TODO Should this function touch the history of the fw?
        m_fw = self.get_fw_by_id(fw_id)
        m_fw.state = 'READY'
        self._replace_fw(m_fw, state='RESERVED', upsert=True)

        self.rerun_fw(m_fw.fw_id, rerun_duplicates=False)

    def set_reservation_id(self, fw_id: int, reservation_id: int, launch_idx: int=-1):
        """
        Set reservation id to the launch corresponding to the given launch id.

        Args:
            launch_id (int)
            reservation_id (int)
        """
        m_fw = self.get_fw_by_id(fw_id, launch_idx)
        m_fw.set_reservation_id(reservation_id)
        self._replace_fw(m_fw)

    def change_launch_dir(self, fw_id: int, launch_dir: str, launch_idx: int=-1):
        """
        Change the launch directory corresponding to the given launch id.

        Args:
            launch_id (int)
            launch_dir (str): path to the new launch directory.
        """
        m_fw = self.get_fw_by_id(fw_id, launch_idx)
        m_fw.launch_dir = launch_dir
        # this only edits a launch, should add a _get_launch and _replace_launch
        self._replace_fw(m_fw, upsert=True)

    def restore_backup_data(self, fw_id: int):
        """
        For the given firework id, restore the back up data.
        """
        if fw_id in self.backup_fw_data:
            self._replace_fw(Firework.from_dict(self.backup_fw_data[fw_id]))

    def get_fw_by_id(self, fw_id: int, launch_idx: int=-1) -> Firework:
        """
        Given a Firework id, give back a Firework object.

        Args:
            fw_id (int): Firework id.

        Returns:
            Firework object
        """
        return Firework.from_dict(self.get_fw_dict_by_id(fw_id, launch_idx))

    def get_wf_by_fw_id(self, fw_id: int) -> Workflow:
        """
        Given a Firework id, give back the Workflow containing that Firework.

        Args:
            fw_id (int)

        Returns:
            A Workflow object
        """
        links_dict = self._find_wf(fw_id)
        if not links_dict:
            raise ValueError("Could not find a Workflow with fw_id: {}".format(fw_id))
        fws = map(self.get_fw_by_id, links_dict["nodes"])
        return Workflow(fws, links_dict['links'], links_dict['name'],
                        links_dict['metadata'], links_dict['created_on'], links_dict['updated_on'])

    def get_wf_by_fw_id_lzyfw(self, fw_id: int) -> Workflow:
        """
        Given a FireWork id, give back the Workflow containing that FireWork.

        Args:
            fw_id (int)

        Returns:
            A Workflow object
        """
        links_dict = self._find_wf(fw_id)
        if not links_dict:
            raise ValueError("Could not find a Workflow with fw_id: {}".format(fw_id))

        fws = []
        for fw_id in links_dict['nodes']:
            fws.append(self._get_lazy_firework(fw_id))
        # Check for fw_states in links_dict to conform with pre-optimized workflows
        if 'fw_states' in links_dict:
            fw_states = dict([(int(k), v) for (k, v) in links_dict['fw_states'].items()])
        else:
            fw_states = None

        return Workflow(fws, links_dict['links'], links_dict['name'],
                        links_dict['metadata'], links_dict['created_on'],
                        links_dict['updated_on'], fw_states)

    def _refresh_wf(self, fw_id: int) -> Union[Dict, None]:
        """#
        Update the FW state of all jobs in workflow.

        Args:
            fw_id (int): the parent fw_id - children will be refreshed
        """
        # TODO: time how long it took to refresh the WF!
        # TODO: need a try-except here, high probability of failure if incorrect action supplied
        try:
            with WFLock(self, fw_id):
                wf = self.get_wf_by_fw_id_lzyfw(fw_id)
                updated_ids = wf.refresh(fw_id)
                self._update_wf(wf, updated_ids)
        except LockedWorkflowError:
            self.m_logger.info("fw_id {} locked. Can't refresh!".format(fw_id))
        except:
            # some kind of internal error - an example is that fws serialization changed due to
            # code updates and thus the Firework object can no longer be loaded from db description
            # Action: *manually* mark the fw and workflow as FIZZLED
            # TODO THIS BEHAVIOR HAS CHANGED SLIGHTLY WITH MY REVISION, MIGHT SET
            # THE FW TO DEFUSED OR JUST SET WORKFLOW STATE. I think there's a bug in the
            # v1 code because if the Workflow is reinstantiated as an object its
            # state won't be what's in the db because of the way the workflow
            # state is determined
            self._internal_fizzle(fw_id)
            import traceback
            err_message = "Error refreshing workflow. The full stack trace is: {}".format(
                traceback.format_exc())
            raise RuntimeError(err_message)

    """ EXTERNALLY CALLABLE FUNCTIONS WITH ABSTRACT DECLARATIONS """

    # TODO NOTE: CHANGED THESE FUNCTION SIGNATURES TO TAKE fw_id's
    # INSTEAD OF launch_id's ETC.

    @property
    @abstractmethod
    def workflow_count(self):
        """
        Number of workflows in the database
        """
        pass

    @property
    @abstractmethod
    def firework_count(self):
        """
        Number of fireworks in the database
        """
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
    def set_priority(self, fw_id: int, priority: int):
        """
        Set priority to the firework with the given id.

        Args:
            fw_id (int): firework id
            priority (int): higher number -> higher priority
        """
        pass

    @abstractmethod
    def get_fw_ids(self, query: Any=None, sort: Optional[List[Tuple[str,str]]] =None,
                   limit: int=0, count_only: bool=False, launches_mode: bool=False) -> List[int]:
        """
        Return all the fw ids that match a query.

        Args:
            query (dict): representing a Mongo query
            sort [(str,str)]: sort argument in Pymongo format
            limit (int): limit the results
            count_only (bool): only return the count rather than explicit ids

        Returns:
            list: list of firework ids matching the query
        """
        pass

    @abstractmethod
    def get_wf_ids(self, query: Any=None, sort: Optional[List[Tuple[str,str]]] =None,
                   limit: int=0, count_only: bool=False) -> List[int]:
        """
        Return one fw id for all workflows that match a query.

        Args:
            query (dict): representing a Mongo query
            sort [(str,str)]: sort argument in Pymongo format
            limit (int): limit the results
            count_only (bool): only return the count rather than explicit ids

        Returns:
            list: list of firework ids
        """
        pass

    @abstractmethod
    def tuneup(self, bkground: bool=True):
        """
        Database tuneup: build indexes
        """
        pass

    # might be able to define functions below here

    @abstractmethod
    def add_offline_run(self, fw_id: int, name: str):
        """
        Add the firework to the offline_run collection.

        Args:
            fw_id (id): firework id
            name (str)
        """
        pass

    @abstractmethod
    def recover_offline(self, fw_id: int, ignore_errors: bool=False,
                        print_errors: bool=False) -> int:
        """
        Update the firework state using the offline data in FW_offline.json file.

        Args:
            fw_id (int): firework id
            ignore_errors (bool)
            print_errors (bool)

        Returns:
            firework id if the recovering fails otherwise None
        """
        pass

    @abstractmethod
    def forget_offline(self, fwid: int):
        """
        Unmark the offline run for the given launch or firework id.

        Args:
            fwid (int): firework id
        """
        pass

    # edit recover_offline to avoid accessing lp.launches and lp.offline_runs
    # add a _reset_warning that optionally gets called at the beginning of the reset
    #   function. This will replace the reset function in lapd_runs.py



    """ INTERNAL FUNCTIONS """

    """ INTERNAL FUNCTIONS FULLY DEFINED HERE """

    def run_exists(self, fworker: Optional[FWorker]=None) -> bool:
        """
        Checks to see if the database contains any FireWorks that are ready to run.

        Returns:
            bool: True if the database contains any FireWorks that are ready to run.
        """
        q = fworker.query if fworker else {}
        return bool(self._get_a_fw_to_run(query=q, checkout=False))

    def future_run_exists(self, fworker: Optional[FWorker]=None) -> bool:
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

    def reserve_fw(self, fworker: FWorker, launch_dir: str,
                   host: Optional[str]=None, ip: Optional[str]=None,
                   fw_id: int=None) -> Tuple[Firework, int]:
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
        return self.checkout_fw(fworker, launch_dir, host=host, ip=ip,
                                fw_id=fw_id, state="RESERVED")

    def mark_fizzled(self, fw_id: int, launch_idx: int=-1):
        """
        Mark the firework corresponding to the given id as FIZZLED.

        Args:
            fw_id (int): firework id

        Returns:
            dict: updated firework
        """
        # Do a confirmed write and make sure state_history is preserved
        self.checkin_fw(fw_id, state='FIZZLED', launch_idx=launch_idx)

    def _upsert_fws(self, fws: List[Firework], reassign_all: bool=False):
        """
        Insert the fireworks to the 'fireworks' collection.

        Args:
            fws ([Firework]): list of fireworks
            reassign_all (bool): if True, reassign the firework ids. The ids are also reassigned
                if the current firework ids are negative.

        Returns:
            dict: mapping between old and new Firework ids
        """
        old_new = {}
        fws.sort(key=lambda x: x.fw_id)

        if reassign_all:
            used_ids = []

            new_id = 0
            prev_id = None
            for fw in fws:
                if fw.fw_id != prev_id:
                    prev_id = fw.fw_id
                    new_id  = self.get_new_fw_id() # used to get all ids at once
                    old_new[fw.fw_id] = new_id
                    used_ids.append(new_id)
                fw.fw_id = new_id
            self._replace_fws(used_ids, fws, upsert=True)
        else:
            for fw in fws:
                prev_id = None
                new_id = 0
                if fw.fw_id < 0:
                    if fw.fw_id != prev_id:
                        new_id = self.get_new_fw_id()
                        prev_id = fw.fw_id
                        old_new[fw.fw_id] = new_id
                    fw.fw_id = new_id
                #self._replace_fw(fw, upsert=True, fw_id=prev_id)
                self._replace_fw(fw, upsert=True)

        return old_new

    def _get_wf_data(self, fw_id: int, mode: str='more') -> Dict:
        """
        Helper function for get_wf_summary_dict
        """
        wf_fields = ["state", "created_on", "name", "nodes"]
        fw_fields = ["state", "fw_id"]
        launch_fields = []

        if mode != "less":
            wf_fields.append("updated_on")
            fw_fields.extend(["name", "launches"])
            launch_fields.append("launch_dir")

        if mode == "reservations":
            launch_fields.append("state_history.reservation_id")

        if mode == "all":
            wf_fields = None
            launch_fields = None

        #wf = self.workflows.find_one({"nodes": fw_id}, projection=wf_fields)
        wf = self._find_wf(fw_id, projection=wf_fields)
        fw_data = []
        id_name_map = {}
        launch_ids = []
        # need to fix this to include only the fireworks with the highest launch indexes
        #for fw in self.fireworks.find({"fw_id": {"$in": wf["nodes"]}}, projection=fw_fields):
        for fw in self._find_fws(wf["nodes"], projection=fw_fields+launch_fields):
            fw_data.append(fw)
            if mode != "less":
                id_name_map[fw["fw_id"]] = "%s--%d" % (fw["name"], fw["fw_id"])

        wf["fw"] = fw_data
        return wf


    """ INTERNAL FUNCTION WITH ABSTRACT DECLARATIONS """

    @abstractmethod
    def _reset(self):
        """
        Helper method to reset the database. Should perform
        all backend-specific reset operations.
        """
        pass

    @abstractmethod
    def _update_wf(self, wf: Workflow, updated_ids: List[int]):
        """
        Update the workflow with the updated firework ids.
        Note: must be called within an enclosing WFLock

        Args:
            wf (Workflow)
            updated_ids ([int]): list of firework ids
        """
        pass

    @abstractmethod
    def _update_fw(self, m_fw, state=None, allowed_states=None, launch_idx=-1,
                    touch_history=True, checkpoint=None):
        pass

    @abstractmethod
    def _internal_fizzle(self, fw_id, launch_idx=-1):
        pass

    @abstractmethod
    def _insert_wfs(self, wfs: Union[Workflow, List[Workflow]]):
        pass

    @abstractmethod
    def _insert_fws(self, fws: Union[Firework, List[Firework]]):
        pass

    @abstractmethod
    def _get_a_fw_to_run(self, query: Optional[Dict]=None, fw_id: Optional[int]=None,
                         launch_idx: int=-1, checkout: bool=True) -> Firework:
        """
        Get the next ready firework to run.

        Args:
            query (dict)
            fw_id (int): If given the query is updated.
                Note: We want to return None if this specific FW  doesn't exist anymore. This is
                because our queue params might have been tailored to this FW.
            checkout (bool): if True, check out the matching firework and set state=RESERVED

        Returns:
            Firework
        """
        pass

    @abstractmethod
    def _delete_wf(self, fw_id, fw_ids):
        pass

    @abstractmethod
    def _checkin_fw(self, fw: Firework, action: FWAction, state: str):
        """
        Helper function for complete_firework
        """
        pass

    @abstractmethod
    def _get_duplicates(self, fw_id: int, include_self: bool=False,
                        allowed_states: Union[List[str], str, None]=None) -> Union[List[int], None]:
        """
        Find duplicates of the Firework with id fw_id
        """
        pass

    @abstractmethod
    def _recover(self, fw_id: int, launch_idx: int=-1):
        """
        ...
        """
        pass

    @abstractmethod
    def _find_fws(self, fw_id: Union[int,List[int]],
                  launch_sort: Optional[int]=-1,
                  allowed_states: Union[List[str], str, None]=None,
                  projection: Optional[Dict]=None
                  ) -> List[Dict]:
        """
        Find the fireworks with the given specifications

        Args:
            fw_id: firework id or list of firework ids
            launch_sort (-1 or 1): whether to sort launch indexes
                by DESCENDING (-1, default) or ASCENDING (1)
            allowed_states (None): optional list of allowed
                states for the fireworks
            projection (None): Optional Mongo dict
                to specify fields to return

        Returns:
            A list of fireworks matching the query info
        """
        pass

    @abstractmethod
    def _find_timeout_fws(self, state: str, expiration_secs: int,
                          query: Optional[Dict]=None):
        """
        Find fireworks that have timed out.

        Args:
            state (str): The Firework state to search for
            expiration_secs (int): Fireworks that entered state
                more than this many seconds ago are considered
                timed out
            query (None): Optional query info for the fireworks.
        """
        pass

    @abstractmethod
    def _find_wf(self, fw_id: int, projection: Optional[Dict]=None,
                 sort: Optional[Dict]=None):
        """
        Find the workflow containing a given firework id.

        Args:
            fw_id: Firework id
            projection (None): Optional Mongo-style field specification
                for return value
            sort (None): Optional Mongo-style sort specifications
        """
        pass

    @abstractmethod
    def _replace_fw(self, m_fw: Firework, state: Optional[str]=None,
                    upsert: bool=False, fw_id: Optional[int]=None):
        """
        Replace a Firework in the database (generally used to update
        many fields or change the fw_id of a firework).

        Args:
            m_fw: Firework to insert
            state (None): If specified, only replace
                the fw if it is in this state
            upsert (False): Whether to upsert in the database
            fw_id (None): If specified, search for this fw_id instead
                of m_fw.fw_id. Use this is fw_id has changed (i.e.
                fw_id is the old id and m_fw.fw_id is the new one)
        """
        pass

    @abstractmethod
    def get_fw_dict_by_id(self, fw_id: int, launch_idx: int=-1) -> Dict:
        """
        Given firework id, return firework dict.

        Args:
            fw_id (int): firework id
            launch_idx (-1): Launch index, default latest launch.
                If <0, gets the -launch_idx most recent launch.
                If >0, searches for an fw with launch_idx

        Returns:
            dict
        """
        pass

    @abstractmethod
    def _get_lazy_firework(self, fw_id: int, launch_idx: int=-1):
        """
        Returns whatever the specific launchpad implementation uses
        """
        pass



    """ LOGGING AND DIRECTORY UTILITIES """

    def get_logdir(self):
        """
        Return the log directory.
        AJ: This is needed for job packing due to Proxy objects not being fully featured...
        """
        return self.logdir

    def log_message(self, level: str, message: str):
        """
        Support for job packing

        Args:
            level (str)
            message (str)
        """
        self.m_logger.log(level, message)

    def get_launchdir(self, fw_id: int, launch_idx: int=-1) -> str:
        """
        Get the launch directory of the firework
        """
        return self.get_fw_by_id(fw_id, launch_idx).launch_dir



    """ USEFUL (BUT NOT REQUIRED) FUNCTIONS """

    def _check_fw_for_uniqueness(self, m_fw: Firework) -> bool:
        """
        Check if there are duplicates. If not unique, a new id is assigned and the workflow
        refreshed.

        Args:
            m_fw (Firework)

        Returns:
            bool: True if the firework is unique
        """
        if not self._steal_launches(m_fw):
            self.m_logger.debug('FW with id: {} is unique!'.format(m_fw.fw_id))
            return True
        self._upsert_fws([m_fw])  # update the DB with the new launches
        self._refresh_wf(m_fw.fw_id)  # since we updated a state, we need to refresh the WF again
        return False
