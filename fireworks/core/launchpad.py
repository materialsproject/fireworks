# coding: utf-8

from __future__ import unicode_literals
from datetime import datetime
from fireworks import Firework, Launch

"""
The LaunchPad manages the FireWorks database.
"""
import datetime
import json
import os
import random
import time
import traceback
from collections import OrderedDict, defaultdict

from pymongo import MongoClient
from pymongo import DESCENDING, ASCENDING

from fireworks.fw_config import LAUNCHPAD_LOC, SORT_FWS, \
    RESERVATION_EXPIRATION_SECS, RUN_EXPIRATION_SECS, MAINTAIN_INTERVAL, WFLOCK_EXPIRATION_SECS, \
    WFLOCK_EXPIRATION_KILL
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

class WFLock(object):
    """
    Lock a Workflow, i.e. for performing update operations
    """

    def __init__(self, lp, fw_id, expire_secs=WFLOCK_EXPIRATION_SECS, kill=WFLOCK_EXPIRATION_KILL):
        self.lp = lp
        self.fw_id = fw_id
        self.expire_secs = expire_secs
        self.kill = kill

    def __enter__(self):
        ctr = 0
        waiting_time = 0
        links_dict = self.lp.workflows.find_and_modify({'nodes': self.fw_id, 'locked': {"$exists": False}},
                                                       {'$set': {'locked': True}})  # acquire lock
        while not links_dict:  # could not acquire lock b/c WF is already locked for writing
            ctr += 1
            time_incr = ctr/10.0+random.random()/100.0
            time.sleep(time_incr)  # wait a bit for lock to free up
            waiting_time += time_incr
            if waiting_time > self.expire_secs:  # too much time waiting, expire lock
                wf = self.lp.workflows.find_one({'nodes': self.fw_id})
                if not wf:
                    raise ValueError("Could not find workflow in database: {}".format(self.fw_id))
                if self.kill:  # force lock aquisition
                    self.lp.m_logger.warn('FORCIBLY ACQUIRING LOCK, WF: {}'.format(self.fw_id))
                    links_dict = self.lp.workflows.find_and_modify({'nodes': self.fw_id},
                                     {'$set': {'locked': True}})
                else:  # throw error if we don't want to force lock acquisition
                    raise ValueError("Could not get workflow - LOCKED: {}".format(self.fw_id))

            else:
                links_dict = self.lp.workflows.find_and_modify({'nodes': self.fw_id, 'locked': {"$exists":False}},
                                                           {'$set': {'locked': True}})  # retry lock

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lp.workflows.find_and_modify({"nodes": self.fw_id}, {"$unset": {"locked": True}})


class LaunchPad(FWSerializable):
    """
    The LaunchPad manages the FireWorks database.
    """

    def __init__(self, host='localhost', port=27017, name='fireworks',
                 username=None, password=None, logdir=None, strm_lvl=None,
                 user_indices=None, wf_user_indices=None):
        """

        :param host:
        :param port:
        :param name:
        :param username:
        :param password:
        :param logdir:
        :param strm_lvl:
        :param user_indices:
        :param wf_user_indices:
        """
        self.host = host
        self.port = port
        self.name = name
        self.username = username
        self.password = password

        # set up logger
        self.logdir = logdir
        self.strm_lvl = strm_lvl if strm_lvl else 'INFO'
        self.m_logger = get_fw_logger('launchpad', l_dir=self.logdir,
                                      stream_level=self.strm_lvl)

        self.user_indices = user_indices if user_indices else []
        self.wf_user_indices = wf_user_indices if wf_user_indices else []

        # get connection
        self.connection = MongoClient(host, port, j=True)
        self.db = self.connection[name]
        if username:
            self.db.authenticate(username, password)

        self.fireworks = self.db.fireworks
        self.launches = self.db.launches
        self.offline_runs = self.db.offline_runs
        self.fw_id_assigner = self.db.fw_id_assigner
        self.workflows = self.db.workflows

        self.backup_launch_data = {}
        self.backup_fw_data = {}

    def to_dict(self):
        """
        Note: usernames/passwords are exported as unencrypted Strings!
        """
        return {
            'host': self.host, 'port': self.port, 'name': self.name,
            'username': self.username, 'password': self.password,
            'logdir': self.logdir, 'strm_lvl': self.strm_lvl,
            'user_indices': self.user_indices,
            'wf_user_indices': self.wf_user_indices}

    def update_spec(self, fw_ids, spec_document):
        """
        Update fireworks with a spec. Sometimes you need to modify a firework
        in progress.

        Args:
            fw_ids: All fw_ids to modify.
            spec_document: The spec document. Note that only modifications to
                the spec key are allowed. So if you supply {
                "_tasks.1.parameter": "hello"}, you are effectively modifying
                spec._tasks.1.parameter in the actual fireworks collection.
        """
        mod_spec = {("spec." + k): v for k, v in spec_document.items()}
        allowed_states = ["READY", "WAITING", "FIZZLED", "DEFUSED"]
        self.fireworks.update({'fw_id': {"$in": fw_ids}, 'state': {"$in": allowed_states}},
                              {"$set": mod_spec}, multi=True)
        for fw in self.fireworks.find({'fw_id': {"$in": fw_ids}, 'state': {"$nin": allowed_states}},
                                      {"fw_id": 1, "state": 1}):
            self.m_logger.warn("Cannot update spec of fw_id: {} with state: {}. "
                               "Try rerunning first".format(fw['fw_id'], fw['state']))

    @classmethod
    def from_dict(cls, d):
        logdir = d.get('logdir', None)
        strm_lvl = d.get('strm_lvl', None)
        user_indices = d.get('user_indices', [])
        wf_user_indices = d.get('wf_user_indices', [])
        return LaunchPad(d['host'], d['port'], d['name'], d['username'],
                         d['password'], logdir, strm_lvl, user_indices,
                         wf_user_indices)

    @classmethod
    def auto_load(cls):
        if LAUNCHPAD_LOC:
            return LaunchPad.from_file(LAUNCHPAD_LOC)
        return LaunchPad()

    def reset(self, password, require_password=True, max_reset_wo_password=25):
        """
        Create a new FireWorks database. This will overwrite the existing FireWorks database! \
        To safeguard against accidentally erasing an existing database, a password must \
        be entered.

        :param password: A String representing today's date, e.g. '2012-12-31'
        :param require_password: Whether a password is required to reset the DB. Setting to false is dangerous because running code unintentionally could clear your DB - use max_reset_wo_password to minimize risk.
        :param max_reset_wo_password: A failsafe: when require_password is set to False, FWS will not clear DBs that contain more workflows than this parameter
        """
        m_password = datetime.datetime.now().strftime('%Y-%m-%d')

        if password == m_password or (not require_password and self.workflows.count() <= max_reset_wo_password):
            self.fireworks.remove()
            self.launches.remove()
            self.workflows.remove()
            self.offline_runs.remove()
            self._restart_ids(1, 1)
            self.tuneup()
            self.m_logger.info('LaunchPad was RESET.')
        elif not require_password:
            raise ValueError("Password check cannot be overridden since the size of DB "
                  "({} workflows) is greater than the max_reset_wo_password "
                  "parameter ({}).".format(self.fireworks.count(), max_reset_wo_password))
        else:
            raise ValueError("Invalid password! Password is today's date: {}".format(m_password))

    def maintain(self, infinite=True, maintain_interval=None):
        maintain_interval = maintain_interval if maintain_interval else MAINTAIN_INTERVAL

        while True:
            self.m_logger.info('Performing maintenance on Launchpad...')

            self.m_logger.debug('Tracking down FIZZLED jobs...')
            fl, ff = self.detect_lostruns(fizzle=True)
            if fl:
                self.m_logger.info('Detected {} FIZZLED launches: {}'.format(len(fl), fl))
                self.m_logger.info('Detected {} FIZZLED FWs: {}'.format(len(ff), ff))

            self.m_logger.debug('Tracking down stuck RESERVED jobs...')
            ur = self.detect_unreserved(rerun=True)
            if ur:
                self.m_logger.info('Unreserved {} RESERVED launches: {}'.format(len(ur), ur))

            self.m_logger.info('LaunchPad was MAINTAINED.')

            if not infinite:
                break

            self.m_logger.debug('Sleeping for {} secs...'.format(maintain_interval))
            time.sleep(maintain_interval)

    def add_wf(self, wf, reassign_all=True):
        """

        :param wf: a Workflow object.
        """
        if isinstance(wf, Firework):
            wf = Workflow.from_FireWork(wf)

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
        self.workflows.insert(wf.to_db_dict())

        self.m_logger.info('Added a workflow. id_map: {}'.format(old_new))
        return old_new

    def add_wf_to_fws(self, new_wf, fw_ids, detour=False, pull_spec_mods=True):
        wf = self.get_wf_by_fw_id(fw_ids[0])
        updated_ids = wf.add_wf_to_fws(new_wf, fw_ids, detour=detour, pull_spec_mods=pull_spec_mods)

        with WFLock(self, fw_ids[0]):
            self._update_wf(wf, updated_ids)

    def get_launch_by_id(self, launch_id):
        """
        Given a Launch id, return details of the Launch

        :param launch_id: launch id
        :return: Launch object
        """
        m_launch = self.launches.find_one({'launch_id': launch_id})
        if m_launch:
            return Launch.from_dict(m_launch)
        raise ValueError('No Launch exists with launch_id: {}'.format(launch_id))

    def get_fw_dict_by_id(self, fw_id):
        fw_dict = self.fireworks.find_one({'fw_id': fw_id})

        if not fw_dict:
            raise ValueError('No Firework exists with id: {}'.format(fw_id))
            # recreate launches from the launch collection

        fw_dict['launches'] = list(self.launches.find(
                    {'launch_id': {"$in": fw_dict['launches']}}))

        fw_dict['archived_launches'] = list(self.launches.find(
                    {'launch_id': {"$in": fw_dict['archived_launches']}}))
        return fw_dict

    def get_fw_by_id(self, fw_id):
        """
        Given a Firework id, give back a Firework object

        :param fw_id: Firework id (int)
        :return: Firework object
        """
        return Firework.from_dict(self.get_fw_dict_by_id(fw_id))

    def get_wf_by_fw_id(self, fw_id):
        """
        Given a Firework id, give back the Workflow containing that Firework
        :param fw_id:
        :return: A Workflow object
        """
        links_dict = self.workflows.find_one({'nodes': fw_id})
        if not links_dict:
            raise ValueError("Could not find a Workflow with fw_id: {}".format(fw_id))
        fws = map(self.get_fw_by_id, links_dict["nodes"])
        return Workflow(fws, links_dict['links'], links_dict['name'],
                        links_dict['metadata'], links_dict['created_on'], links_dict['updated_on'])

    def get_wf_by_fw_id_lzyfw(self, fw_id):
        """
        Given a FireWork id, give back the Workflow containing that FireWork
        :param fw_id:
        :return: A Workflow object
        """
        links_dict = self.workflows.find_one({'nodes': fw_id})
        if not links_dict:
            raise ValueError("Could not find a Workflow with fw_id: {}".format(fw_id))

        fws = []
        for fw_id in links_dict['nodes']:
            fws.append(LazyFirework(fw_id, self.fireworks, self.launches))
        # Check for fw_states in links_dict to conform with preoptimized workflows
        if 'fw_states' in links_dict:
            fw_states = dict([(int(k), v) for (k, v) in links_dict['fw_states'].items()])
        else:
            fw_states = None

        return Workflow(fws, links_dict['links'], links_dict['name'],
                        links_dict['metadata'], links_dict['created_on'],
                        links_dict['updated_on'], fw_states)

    def delete_wf(self, fw_id):
        links_dict = self.workflows.find_one({'nodes': fw_id})
        fw_ids = links_dict["nodes"]
        potential_launch_ids = []
        launch_ids = []
        for i in fw_ids:
            fw_dict = self.fireworks.find_one({'fw_id': i})
            potential_launch_ids += fw_dict["launches"] + fw_dict['archived_launches']

        for i in potential_launch_ids:  # only remove launches if no ohter fws refer to them
            if not self.fireworks.find_one({'$or': [{"launches": i}, {'archived_launches': i}],
                                            'fw_id': {"$nin": fw_ids}}, {'launch_id': 1}):
                launch_ids.append(i)

        print("Remove fws %s" % fw_ids)
        print("Remove launches %s" % launch_ids)
        print("Removing workflow.")
        self.launches.remove({'launch_id': {"$in": launch_ids}})
        self.fireworks.remove({"fw_id": {"$in": fw_ids}})
        self.workflows.remove({'nodes': fw_id})

    def get_wf_summary_dict(self, fw_id, mode="more"):
        """
        A much faster way to get summary information about a Workflow by
        querying only for needed information.

        Args:
            fw_id (int): A Firework id.
            mode (str): Choose between "more", "less" and "all" in terms of
                quantity of information.

        Returns:
            (dict) of information about Workflow.
        """
        wf_fields = ["state", "created_on", "name", "nodes"]
        fw_fields = ["state", "fw_id"]
        launch_fields = []

        if mode != "less":
            wf_fields.append("updated_on")
            fw_fields.extend(["name", "launches"])
            launch_fields.append("launch_id")
            launch_fields.append("launch_dir")

        if mode == "reservations":
            launch_fields.append("state_history.reservation_id")

        if mode == "all":
            wf_fields = None

        wf = self.workflows.find_one({"nodes": fw_id}, projection=wf_fields)
        fw_data = []
        id_name_map = {}
        launch_ids = []
        for fw in self.fireworks.find({"fw_id": {"$in": wf["nodes"]}},
                                      projection=fw_fields):
            if launch_fields:
                launch_ids.extend(fw["launches"])
            fw_data.append(fw)
            if mode != "less":
                id_name_map[fw["fw_id"]] = "%s--%d" % (fw["name"], fw["fw_id"])

        if launch_fields:
            launch_info = defaultdict(list)
            for l in self.launches.find({'launch_id': {"$in": launch_ids}},
                                        projection=launch_fields):
                for i, fw in enumerate(fw_data):
                    if l["launch_id"] in fw["launches"]:
                        launch_info[i].append(l)
            for k, v in launch_info.items():
                fw_data[k]["launches"] = v

        wf["fw"] = fw_data

        # Post process the summary dict so that it "looks" better.
        if mode == "less":
            wf["states_list"] = "-".join(
                [fw["state"][:3] if fw["state"].startswith("R")
                 else fw["state"][0] for fw in wf["fw"]])
            del wf["nodes"]
        elif mode == "more":
            wf["states"] = OrderedDict()
            wf["launch_dirs"] = OrderedDict()
            for fw in wf["fw"]:
                k = "%s--%d" % (fw["name"], fw["fw_id"])
                wf["states"][k] = fw["state"]
                wf["launch_dirs"][k] = [l["launch_dir"] for l in fw[
                    "launches"]]
            del wf["nodes"]
        elif mode == "all":
            wf["links"] = {id_name_map[int(k)]: [id_name_map[i] for i in v]
                           for k, v in wf["links"].items()}
            wf["nodes"] = map(id_name_map.get, wf["nodes"])
            wf["parent_links"] = {
                id_name_map[int(k)]: [id_name_map[i] for i in v]
                for k, v in wf["parent_links"].items()}
        elif mode == "reservations":
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

    def get_fw_ids(self, query=None, sort=None, limit=0, count_only=False):
        """
        Return all the fw ids that match a query,
        :param query: (dict) representing a Mongo query
        :param sort: [(str,str)] sort argument in Pymongo format
        :param limit: (int) limit the results
        :param count_only: (bool) only return the count rather than explicit ids
        """
        fw_ids = []
        criteria = query if query else {}

        if count_only:
            if limit:
                return ValueError("Cannot count_only and limit at the same time!")
            return self.fireworks.find(criteria, {}, sort=sort).count()

        for fw in self.fireworks.find(criteria, {"fw_id": True}, sort=sort).limit(limit):
            fw_ids.append(fw["fw_id"])
        return fw_ids

    def get_wf_ids(self, query=None, sort=None, limit=0, count_only=False):
        """
        Return one fw id for all workflows that match a query,
        :param query: (dict) representing a Mongo query
        :param sort: [(str,str)] sort argument in Pymongo format
        :param limit: (int) limit the results
        :param count_only: (bool) only return the count rather than explicit ids
        """
        wf_ids = []
        criteria = query if query else {}
        if count_only:
            return self.workflows.find(criteria, {"nodes": True}, sort=sort).limit(limit).count()

        for fw in self.workflows.find(criteria, {"nodes": True}, sort=sort).limit(limit):
            wf_ids.append(fw["nodes"][0])

        return wf_ids

    def run_exists(self, fworker=None):
        """
        Checks to see if the database contains any FireWorks that are ready to run
        :return: (T/F)
        """
        q = fworker.query if fworker else {}
        return bool(self._get_a_fw_to_run(query=q, checkout=False))

    def tuneup(self, bkground=True):
        self.m_logger.info('Performing db tune-up')

        self.m_logger.debug('Updating indices...')
        self.fireworks.ensure_index('fw_id', unique=True, background=bkground)
        for f in ("state", 'spec._category', 'created_on', 'updated_on' 'name', 'launches'):
            self.fireworks.ensure_index(f, background=bkground)

        self.launches.ensure_index('launch_id', unique=True, background=bkground)
        self.launches.ensure_index('fw_id', background=bkground)
        self.launches.ensure_index('state_history.reservation_id', background=bkground)

        for f in ('state', 'time_start', 'time_end', 'host', 'ip',
                  'fworker.name'):
            self.launches.ensure_index(f, background=bkground)

        for f in ('name', 'created_on', 'updated_on', 'nodes'):
            self.workflows.ensure_index(f, background=bkground)

        for idx in self.user_indices:
            self.fireworks.ensure_index(idx, background=bkground)

        for idx in self.wf_user_indices:
            self.workflows.ensure_index(idx, background=bkground)

        # for frontend, which needs to sort on _id after querying on state
        self.fireworks.ensure_index([("state", DESCENDING), ("_id", DESCENDING)], background=bkground)
        self.fireworks.ensure_index([("state", DESCENDING), ("spec._priority", DESCENDING), ("created_on", DESCENDING)], background=bkground)
        self.fireworks.ensure_index([("state", DESCENDING), ("spec._priority", DESCENDING), ("created_on", ASCENDING)], background=bkground)
        self.workflows.ensure_index([("state", DESCENDING), ("_id", DESCENDING)], background=bkground)

        if not bkground:
            self.m_logger.debug('Compacting database...')
            try:
                self.db.command({'compact': 'fireworks'})
                self.db.command({'compact': 'launches'})
            except:
                self.m_logger.debug('Database compaction failed (not critical)')

    def defuse_fw(self, fw_id, rerun_duplicates=True):
        allowed_states = ['DEFUSED', 'WAITING', 'READY', 'FIZZLED']
        f = self.fireworks.find_and_modify(
            {'fw_id': fw_id, 'state': {'$in': allowed_states}},
            {'$set': {'state': 'DEFUSED', 'updated_on': datetime.datetime.utcnow()}})
        if f:
            self._refresh_wf(fw_id)

        if not f:
            self.rerun_fw(fw_id, rerun_duplicates)
            f = self.fireworks.find_and_modify(
            {'fw_id': fw_id, 'state': {'$in': allowed_states}},
            {'$set': {'state': 'DEFUSED', 'updated_on': datetime.datetime.utcnow()}})
            if f:
                self._refresh_wf(fw_id)

        return f

    def reignite_fw(self, fw_id):
        f = self.fireworks.find_and_modify({'fw_id': fw_id, 'state': 'DEFUSED'},
                                           {'$set': {'state': 'WAITING',
                                                     'updated_on': datetime.datetime.utcnow()}})
        if f:
            self._refresh_wf(fw_id)
        return f

    def defuse_wf(self, fw_id):
        wf = self.get_wf_by_fw_id_lzyfw(fw_id)
        for fw in wf.fws:
            self.defuse_fw(fw.fw_id)

        self._refresh_wf(fw_id)

    def reignite_wf(self, fw_id):
        wf = self.get_wf_by_fw_id_lzyfw(fw_id)
        for fw in wf.fws:
            self.reignite_fw(fw.fw_id)

    def archive_wf(self, fw_id):
        # first archive all the launches, so they are not used in duplicate checks
        wf = self.get_wf_by_fw_id_lzyfw(fw_id)
        if wf.state != 'ARCHIVED':
            fw_ids = [f.fw_id for f in wf.fws]
            for fw_id in fw_ids:
                self.rerun_fw(fw_id)

            # second set the state of all FWs to ARCHIVED
            wf = self.get_wf_by_fw_id_lzyfw(fw_id)
            for fw in wf.fws:
                self.fireworks.find_and_modify({'fw_id': fw.fw_id},
                                               {'$set': {'state': 'ARCHIVED',
                                                         'updated_on': datetime.datetime.utcnow()}})

                self._refresh_wf(fw.fw_id)

    def _restart_ids(self, next_fw_id, next_launch_id):
        """
        (internal method) Used to reset id counters

        :param next_fw_id: id to give next Firework (int)
        :param next_launch_id: id to give next Launch (int)
        """
        self.fw_id_assigner.remove()
        self.fw_id_assigner.find_and_modify({'_id': -1}, {'next_fw_id': next_fw_id,
                                                          'next_launch_id': next_launch_id},
                                            upsert=True)
        self.m_logger.debug(
            'RESTARTED fw_id, launch_id to ({}, {})'.format(next_fw_id, next_launch_id))

    def _check_fw_for_uniqueness(self, m_fw):
        # check if there are duplicates
        if not self._steal_launches(m_fw):
            self.m_logger.debug('FW with id: {} is unique!'.format(m_fw.fw_id))
            return True

        self._upsert_fws([m_fw])  # update the DB with the new launches
        self._refresh_wf(m_fw.fw_id)  # since we updated a state, we need to refresh the WF again

        return False

    def _get_a_fw_to_run(self, query=None, fw_id=None, checkout=True):
        m_query = dict(query) if query else {}  # make a defensive copy
        m_query['state'] = 'READY'

        sortby = [("spec._priority", DESCENDING)]

        if SORT_FWS.upper() == "FIFO":
            sortby.append(("created_on", ASCENDING))

        elif SORT_FWS.upper() == "FILO":
            sortby.append(("created_on", DESCENDING))

        # Override query if fw_id defined
        # Note for the fw_id option: We want to return None if this specific FW doesn't exist anymore
        # This is because our queue params might have been tailored to this FW
        if fw_id:
            m_query = {"fw_id": fw_id, "state": {'$in': ['READY', 'RESERVED']}}

        while True:
            # check out the matching firework, depending on the query set by the FWorker
            if checkout:
                m_fw = self.fireworks.find_and_modify(m_query,
                                                      {'$set': {'state': 'RESERVED',
                                                       'updated_on': datetime.datetime.utcnow()}},
                                                      sort=sortby)
            else:
                m_fw = self.fireworks.find_one(m_query, {'fw_id': 1, 'spec': 1},
                                               sort=sortby)

            if not m_fw:
                return None

            m_fw = self.get_fw_by_id(m_fw['fw_id'])
            if self._check_fw_for_uniqueness(m_fw):
                return m_fw

    def reserve_fw(self, fworker, launch_dir, host=None, ip=None):
        m_fw = self._get_a_fw_to_run(fworker.query)
        if not m_fw:
            return None, None
            # create a launch
        # TODO: this code is duplicated with checkout_fw with minimal mods, should refactor this!!
        launch_id = self.get_new_launch_id()
        trackers = [Tracker.from_dict(f) for f in m_fw.spec['_trackers']] if '_trackers' in m_fw.spec else None
        m_launch = Launch('RESERVED', launch_dir, fworker, host, ip, trackers=trackers, launch_id=launch_id,
                          fw_id=m_fw.fw_id)
        self.launches.find_and_modify({'launch_id': m_launch.launch_id}, m_launch.to_db_dict(), upsert=True)

        # add launch to FW
        m_fw.launches.append(m_launch)
        m_fw.state = 'RESERVED'
        self._upsert_fws([m_fw])
        self.m_logger.debug('Reserved FW with id: {}'.format(m_fw.fw_id))

        return m_fw, launch_id

    def get_fw_ids_from_reservation_id(self, reservation_id):
        fw_ids = []
        l_id = self.launches.find_one({"state_history.reservation_id": reservation_id}, {'launch_id': 1})['launch_id']
        for fw in self.fireworks.find({'launches': l_id}, {'fw_id': 1}):
            fw_ids.append(fw['fw_id'])

        return fw_ids

    def cancel_reservation_by_reservation_id(self, reservation_id):
        l_id = self.launches.find_one({"state_history.reservation_id": reservation_id, "state": "RESERVED"}, {'launch_id': 1})
        if l_id:
            self.cancel_reservation(l_id['launch_id'])
        else:
            self.m_logger.info("Can't find any reserved jobs with reservation id: {}".format(reservation_id))

    def get_reservation_id_from_fw_id(self, fw_id):
        fw = self.fireworks.find_one({'fw_id': fw_id}, {'launches': 1})
        if fw:
            for l in self.launches.find({'launch_id': {'$in': fw['launches']}}, {'state_history': 1}):
                for d in l['state_history']:
                    if 'reservation_id' in d:
                        return d['reservation_id']

    def cancel_reservation(self, launch_id):
        m_launch = self.get_launch_by_id(launch_id)
        m_launch.state = 'READY'
        self.launches.find_and_modify({'launch_id': m_launch.launch_id, "state": "RESERVED"}, m_launch.to_db_dict(), upsert=True)

        for fw in self.fireworks.find({'launches': launch_id, 'state': 'RESERVED'}, {'fw_id': 1}):
            self.rerun_fw(fw['fw_id'], rerun_duplicates=False)

    def detect_unreserved(self, expiration_secs=RESERVATION_EXPIRATION_SECS, rerun=False):
        bad_launch_ids = []
        now_time = datetime.datetime.utcnow()
        cutoff_timestr = (now_time - datetime.timedelta(seconds=expiration_secs)).isoformat()
        bad_launch_data = self.launches.find({'state': 'RESERVED', 'state_history': {
            '$elemMatch': {'state': 'RESERVED', 'updated_on': {'$lte': cutoff_timestr}}}},
                                             {'launch_id': 1})
        for ld in bad_launch_data:
            bad_launch_ids.append(ld['launch_id'])
        if rerun:
            for lid in bad_launch_ids:
                self.cancel_reservation(lid)
        return bad_launch_ids

    def mark_fizzled(self, launch_id):
        # TODO: this seems a lot like the code in complete_launch...DRY

        # Do a confirmed write and make sure state_history is preserved
        m_launch = self.get_launch_by_id(launch_id)
        m_launch.state = 'FIZZLED'
        self.launches.find_and_modify({'launch_id': m_launch.launch_id}, m_launch.to_db_dict(), upsert=True)

        for fw_data in self.fireworks.find({'launches': launch_id}, {'fw_id': 1}):
            self._refresh_wf(fw_data['fw_id'])

    def detect_lostruns(self, expiration_secs=RUN_EXPIRATION_SECS, fizzle=False, rerun=False, max_runtime=None, min_runtime=None):
        lost_launch_ids = []
        lost_fw_ids = []
        potential_lost_fw_ids = []
        now_time = datetime.datetime.utcnow()
        cutoff_timestr = (now_time - datetime.timedelta(seconds=expiration_secs)).isoformat()
        bad_launch_data = self.launches.find({'state': 'RUNNING', 'state_history': {
            '$elemMatch': {'state': 'RUNNING', 'updated_on': {'$lte': cutoff_timestr}}}},
                                             {'launch_id': 1, 'fw_id': 1})

        for ld in bad_launch_data:
            bad_launch = True
            if max_runtime or min_runtime:
                bad_launch = False
                m_l = self.get_launch_by_id(ld['launch_id'])
                utime = m_l._get_time('RUNNING', use_update_time=True)
                ctime = m_l._get_time('RUNNING', use_update_time=False)
                if (not max_runtime or (utime-ctime).seconds <= max_runtime) \
                        and (not min_runtime or (utime-ctime).seconds >= min_runtime):
                    bad_launch = True

            if bad_launch:
                lost_launch_ids.append(ld['launch_id'])
                potential_lost_fw_ids.append(ld['fw_id'])

        for fw_id in potential_lost_fw_ids:  # tricky: figure out what's actually lost
            f = self.fireworks.find_one({"fw_id": fw_id}, {"launches": 1, "state": 1})
            if f['state'] == "RUNNING":  # only RUNNING FireWorks can be "lost", i.e. not defused or archived
                l_ids = f["launches"]
                not_lost = [x for x in l_ids if x not in lost_launch_ids]
                if len(not_lost) == 0:  # all launches are lost - we are lost!
                    lost_fw_ids.append(fw_id)
                else:
                    for l_id in not_lost:
                        l_state = self.launches.find_one({"launch_id": l_id}, {"state": 1})['state']
                        if Firework.STATE_RANKS[l_state] > Firework.STATE_RANKS['FIZZLED']:
                            break
                    else:
                        lost_fw_ids.append(fw_id)  # all Launches not lost are anyway FIZZLED / ARCHIVED

        if fizzle or rerun:
            for lid in lost_launch_ids:
                self.mark_fizzled(lid)
                if rerun:
                    fw_id = self.launches.find_one({"launch_id": lid}, {"fw_id": 1})['fw_id']
                    if fw_id in lost_fw_ids:
                        self.rerun_fw(fw_id)

        return lost_launch_ids, lost_fw_ids

    def set_reservation_id(self, launch_id, reservation_id):
        m_launch = self.get_launch_by_id(launch_id)
        m_launch.set_reservation_id(reservation_id)
        self.launches.find_and_modify({'launch_id': launch_id}, m_launch.to_db_dict())

    def checkout_fw(self, fworker, launch_dir, fw_id=None, host=None, ip=None):
        """
        (internal method) Finds a Firework that's ready to be run, marks it as running,
        and returns it to the caller. The caller is responsible for running the Firework.

        :param fworker: A FWorker instance
        :param host: the host making the request (for creating a Launch object)
        :param ip: the ip making the request (for creating a Launch object)
        :param launch_dir: the dir the FW will be run in (for creating a Launch object)
        :return: a Firework, launch_id tuple
        """

        # TODO: this method is confusing, says AJ of Xmas past. Clean it up, remove duplication, etc.

        m_fw = self._get_a_fw_to_run(fworker.query, fw_id)
        if not m_fw:
            return None, None

        # was this Launch previously reserved? If so, overwrite that reservation with this Launch
        # note that adding a new Launch is problematic from a duplicate run standpoint
        prev_reservations = [l for l in m_fw.launches if l.state == 'RESERVED']
        reserved_launch = None if len(prev_reservations) == 0 else prev_reservations[0]

        state_history = reserved_launch.state_history if reserved_launch else None
        l_id = reserved_launch.launch_id if reserved_launch else self.get_new_launch_id()
        trackers = [Tracker.from_dict(f) for f in m_fw.spec['_trackers']] if '_trackers' in m_fw.spec else None
        m_launch = Launch('RUNNING', launch_dir, fworker, host, ip, trackers=trackers, state_history=state_history,
                          launch_id=l_id,
                          fw_id=m_fw.fw_id)

        self.launches.find_and_modify({'launch_id': m_launch.launch_id}, m_launch.to_db_dict(), upsert=True)

        self.m_logger.debug('Created/updated Launch with launch_id: {}'.format(l_id))

        if not reserved_launch:
            # we're appending a new Firework
            m_fw.launches.append(m_launch)
        else:
            # we're updating an existing launch
            m_fw.launches = [m_launch if l.launch_id == m_launch.launch_id else l for l in
                             m_fw.launches]

        m_fw.state = 'RUNNING'
        self._upsert_fws([m_fw])
        self._refresh_wf(m_fw.fw_id)

        # update any duplicated runs
        for fw in self.fireworks.find(
                {'launches': l_id, 'state': {'$in': ['WAITING', 'READY', 'RESERVED', 'FIZZLED']}},
                {'fw_id': 1}):
            fw_id = fw['fw_id']
            fw = self.get_fw_by_id(fw_id)
            fw.state = 'RUNNING'
            self._upsert_fws([fw])
            self._refresh_wf(fw.fw_id)

        self.m_logger.debug('Checked out FW with id: {}'.format(m_fw.fw_id))

        # Store backup copies of the initial data for retrieval in case of failure
        self.backup_launch_data[m_launch.launch_id] = m_launch.to_db_dict()
        self.backup_fw_data[fw_id] = m_fw.to_db_dict()

        # use dict as return type, just to be compatible with multiprocessing
        return m_fw, l_id

    def change_launch_dir(self, launch_id, launch_dir):
        m_launch = self.get_launch_by_id(launch_id)
        m_launch.launch_dir = launch_dir
        self.launches.find_and_modify({'launch_id': m_launch.launch_id}, m_launch.to_db_dict(), upsert=True)

    def restore_backup_data(self, launch_id, fw_id):
        if launch_id in self.backup_launch_data:
            self.launches.find_and_modify({'launch_id': launch_id}, self.backup_launch_data[launch_id])
        if fw_id in self.backup_fw_data:
            self.fireworks.find_and_modify({'fw_id': fw_id}, self.backup_fw_data[fw_id])

    def complete_launch(self, launch_id, action, state='COMPLETED'):
        """
        (internal method) used to mark a Firework's Launch as completed.
        :param launch_id:
        :param action: the FWAction of what to do next
        """
        # update the launch data to COMPLETED, set end time, etc
        m_launch = self.get_launch_by_id(launch_id)
        m_launch.state = state
        m_launch.action = action
        self.launches.find_and_modify({'launch_id': m_launch.launch_id}, m_launch.to_db_dict(), upsert=True)

        # find all the fws that have this launch
        for fw in self.fireworks.find({'launches': launch_id}, {'fw_id': 1}):
            fw_id = fw['fw_id']
            self._refresh_wf(fw_id)
        # change return type to dict to make return type seriazlizable to
        # support job packing
        return m_launch.to_dict()

    def ping_launch(self, launch_id, ptime=None):
        m_launch = self.get_launch_by_id(launch_id)
        for tracker in m_launch.trackers:
            tracker.track_file(m_launch.launch_dir)

        m_launch.touch_history(ptime)
        self.launches.update({'launch_id': launch_id, 'state': 'RUNNING'},
            {'$set':{'state_history':m_launch.to_db_dict()['state_history'], 'trackers': [t.to_dict() for t in m_launch.trackers]}})

    def get_new_fw_id(self):
        """
        Checkout the next Firework id
        """
        try:
            return self.fw_id_assigner.find_and_modify({}, {'$inc': {'next_fw_id': 1}})['next_fw_id']
        except:
            raise ValueError("Could not get next FW id! If you have not yet initialized the database, please do so by performing a database reset (e.g., lpad reset)")

    def get_new_launch_id(self):
        """
        Checkout the next Launch id
        """
        try:
            return self.fw_id_assigner.find_and_modify({}, {'$inc': {'next_launch_id': 1}})['next_launch_id']
        except:
            raise ValueError("Could not get next launch id! If you have not yet initialized the database, please do so by performing a database reset (e.g., lpad reset)")

    def _upsert_fws(self, fws, reassign_all=False):
        old_new = {} # mapping between old and new Firework ids

        # sort the FWs by id, then the new FW_ids will match the order of the old ones...
        fws.sort(key=lambda x: x.fw_id)

        for fw in fws:
            if fw.fw_id < 0 or reassign_all:
                new_id = self.get_new_fw_id()
                old_new[fw.fw_id] = new_id
                fw.fw_id = new_id
            self.fireworks.find_and_modify({'fw_id': fw.fw_id}, fw.to_db_dict(), upsert=True)

        return old_new

    def rerun_fw(self, fw_id, rerun_duplicates=True):
        m_fw = self.fireworks.find_one({"fw_id": fw_id}, {"state": 1})
        # detect FWs that share the same launch. Must do this before rerun
        duplicates = []
        reruns = []
        if rerun_duplicates:
            f = self.fireworks.find_one({"fw_id": fw_id, "spec._dupefinder": {"$exists": True}}, {'launches':1})
            if f:
                for d in self.fireworks.find({"launches": {"$in": f['launches']}, "fw_id": {"$ne": fw_id}}, {"fw_id": 1}):
                    duplicates.append(d['fw_id'])
            duplicates = list(set(duplicates))
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
            r = self.rerun_fw(f, rerun_duplicates=False)  # False for speed, True shouldn't be needed
            reruns.extend(r)

        return reruns  # return the ids that were rerun

    def rerun_fws_task_level(self, fw_id, rerun_duplicates=True, launch_id=None, recover_mode=None):
        """
        Rerun a fw at the task level
        :param fw_id: (int) fw_id to rerun
        :param rerun_duplicates: (bool) also rerun duplicate FWs
        :param launch_id: (int) launch id to rerun, if known. otherwise the last launch_id will be used
        :param recover_mode: (str) use "prev_dir" to run again in previous dir, "cp" to try to copy data to new dir, or None to start from scratch
        :return: ([int]) list of rerun fw_ids
        """
        m_fw = self.get_fw_by_id(fw_id)

        # check if task_level parameters are properly defined
        if not launch_id:
            try:
                launch_id = m_fw.launches[-1].launch_id
            except:
                traceback.print_exc()
                self.m_logger.info("Can't find a launch to recover fw_id {}. Skipping...".format(fw_id))
                return None
        elif launch_id not in [l.launch_id for l in m_fw.launches+m_fw.archived_launches]:
            self.m_logger.info("Launch id {} not existent for m_fw {}. Skipping...".format(launch_id, fw_id))
            return None
        # check if the failed task information is available, can't recover otherwise
        if self.get_launch_by_id(launch_id).action.stored_data.get('_exception', {}).get('_failed_task_n', None) is None:
            self.m_logger.info("No information to recover launch id {} for m_fw {}. Skipping..."
                               .format(launch_id, fw_id))
            return None

        #rerun jobs and duplicates
        reruns = self.rerun_fw(fw_id, rerun_duplicates)

        # if rerun was fine, set the task_level parameters
        if reruns:
            set_spec = {'$set': {'spec._recover_launch._launch_id': launch_id,
                                 'spec._recover_launch._recover_mode': recover_mode}}
            if recover_mode == 'prev_dir':
                set_spec['$set']['spec._launch_dir'] = self.get_launch_by_id(launch_id).launch_dir

            self.fireworks.find_and_modify({"fw_id": fw_id}, set_spec)

        return reruns

    def _refresh_wf(self, fw_id):

        """
        Update the FW state of all jobs in workflow
        :param fw_id: the parent fw_id - children will be refreshed
        """
        # TODO: time how long it took to refresh the WF!
        # TODO: need a try-except here, high probability of failure if incorrect action supplied
        with WFLock(self, fw_id):
            wf = self.get_wf_by_fw_id_lzyfw(fw_id)
            updated_ids = wf.refresh(fw_id)
            self._update_wf(wf, updated_ids)


    def _update_wf(self, wf, updated_ids):
        # note: must be called within an enclosing WFLock

        updated_fws = [wf.id_fw[fid] for fid in updated_ids]
        old_new = self._upsert_fws(updated_fws)
        wf._reassign_ids(old_new)

        # find a node for which the id did not change, so we can query on it to get WF
        query_node = None
        for f in wf.id_fw:
            if f not in old_new.values() or old_new.get(f, None) == f:
                query_node = f
                break

        assert query_node is not None
        if not self.workflows.find_one({'nodes': query_node}):
            raise ValueError("BAD QUERY_NODE! {}".format(query_node))
        # redo the links
        wf = wf.to_db_dict()
        wf['locked'] = True  # preserve the lock!
        self.workflows.find_and_modify({'nodes': query_node}, wf)


    def _steal_launches(self, thief_fw):
        stolen = False
        if thief_fw.state in ['READY', 'RESERVED'] and '_dupefinder' in thief_fw.spec:
            m_dupefinder = thief_fw.spec['_dupefinder']
            # get the query that will limit the number of results to check as duplicates
            m_query = m_dupefinder.query(thief_fw.spec)
            m_query['launches'] = {'$ne': []}
            # iterate through all potential duplicates in the DB
            self.m_logger.debug('Querying for duplicates, fw_id: {}'.format(thief_fw.fw_id))
            for potential_match in self.fireworks.find(m_query):
                self.m_logger.debug(
                    'Verifying for duplicates, fw_ids: {}, {}'.format(thief_fw.fw_id,
                                                                      potential_match['fw_id']))
                spec1 = dict(thief_fw.to_dict()['spec'])  # defensive copy
                spec2 = dict(potential_match['spec'])  # defensive copy
                if m_dupefinder.verify(spec1, spec2):  # verify the match
                    # steal the launches
                    victim_fw = self.get_fw_by_id(potential_match['fw_id'])
                    thief_launches = [l.launch_id for l in thief_fw.launches]
                    valuable_launches = [l for l in victim_fw.launches if
                                         l.launch_id not in thief_launches]
                    for launch in valuable_launches:
                        thief_fw.launches.append(launch)
                        stolen = True
                        self.m_logger.info(
                            'Duplicate found! fwids {} and {}'.format(thief_fw.fw_id,
                                                                      potential_match['fw_id']))
        return stolen

    def set_priority(self, fw_id, priority):
        self.fireworks.find_and_modify({"fw_id": fw_id}, {'$set': {'spec._priority': priority}})

    def get_logdir(self):
        # AJ: This is needed for job packing due to Proxy objects not being fully featured...
        return self.logdir

    def add_offline_run(self, launch_id, fw_id, name):
        d = {'fw_id': fw_id}
        d['launch_id'] = launch_id
        d['name'] = name
        d['created_on'] = datetime.datetime.utcnow().isoformat()
        d['updated_on'] = datetime.datetime.utcnow().isoformat()
        d['deprecated'] = False
        d['completed'] = False
        self.offline_runs.insert(d)

    def recover_offline(self, launch_id, ignore_errors=False):
        # get the launch directory
        m_launch = self.get_launch_by_id(launch_id)
        try:
            self.m_logger.debug("RECOVERING fw_id: {}".format(m_launch.fw_id))
            # look for ping file - update the Firework if this is the case
            ping_loc = os.path.join(m_launch.launch_dir, "FW_ping.json")
            if os.path.exists(ping_loc):
                with open(ping_loc) as f:
                    ping_time = reconstitute_dates(json.loads(f.read())['ping_time'])
                    self.ping_launch(launch_id, ping_time)

            # look for action in FW_offline.json
            offline_loc = os.path.join(m_launch.launch_dir, "FW_offline.json")
            with open(offline_loc) as f:
                offline_data = json.loads(f.read())
                if 'started_on' in offline_data:
                    m_launch.state = 'RUNNING'
                    for s in m_launch.state_history:
                        if s['state'] == 'RUNNING':
                            s['created_on'] = reconstitute_dates(offline_data['started_on'])
                    self.launches.find_and_modify({'launch_id': m_launch.launch_id}, m_launch.to_db_dict(), upsert=True)

                if 'fwaction' in offline_data:
                    fwaction = FWAction.from_dict(offline_data['fwaction'])
                    state = offline_data['state']
                    m_launch = Launch.from_dict(
                        self.complete_launch(launch_id, fwaction, state))
                    for s in m_launch.state_history:
                        if s['state'] == offline_data['state']:
                            s['created_on'] = reconstitute_dates(offline_data['completed_on'])
                    self.launches.find_and_modify({'launch_id': m_launch.launch_id}, m_launch.to_db_dict(), upsert=True)
                    self.offline_runs.update({"launch_id": launch_id}, {"$set": {"completed":True}})

            # update the updated_on
            self.offline_runs.update({"launch_id": launch_id}, {"$set": {"updated_on": datetime.datetime.utcnow().isoformat()}})
            return None
        except:
            if not ignore_errors:
                traceback.print_exc()
                m_action = FWAction(stored_data={'_message': 'runtime error during task', '_task': None,
                                                     '_exception': {'_stacktrace': traceback.format_exc(),
                                                     '_details': None}}, exit=True)
                self.complete_launch(launch_id, m_action, 'FIZZLED')
                self.offline_runs.update({"launch_id": launch_id}, {"$set": {"completed":True}})
            return m_launch.fw_id

    def forget_offline(self, fw_id):
        self.offline_runs.update({"fw_id": fw_id}, {"$set": {"deprecated":True}})

    def get_tracker_data(self, fw_id):
        data = []
        for l in self.launches.find({'fw_id': fw_id}, {'trackers': 1, 'launch_id': 1}):
            if 'trackers' in l:  # backwards compatibility
                trackers = [Tracker.from_dict(t) for t in l['trackers']]
                data.append({'launch_id': l['launch_id'], 'trackers': trackers})

        return data

    # support for job packing
    def log_message(self, level, message):
        self.m_logger.log(level, message)


class LazyFirework(object):
    """
    A LazyFirework only has the fw_id, and grabs other data just-in-time.
    This representation can speed up Workflow loading as only "important" FWs need to be
    fully loaded.
    :param fw_id:
    :param fw_coll:
    :param launch_coll:
    """

    # Get these fields from DB when creating new FireWork object
    db_fields = ('name', 'fw_id', 'spec', 'created_on', 'state')
    db_launch_fields = ('launches', 'archived_launches')

    def __init__(self, fw_id, fw_coll, launch_coll):
        # This is the only attribute known w/o a DB query
        self.fw_id = fw_id

        self._fwc, self._lc = fw_coll, launch_coll
        self._launches = {k: False for k in self.db_launch_fields}
        self._fw, self._lids = None, None

    # FireWork methods

    @property
    def state(self):
        return self.partial_fw._state

    @state.setter
    def state(self, state):
        self.partial_fw._state = state
        self.partial_fw.updated_on = datetime.datetime.utcnow()

    def to_dict(self):
        return self.full_fw.to_dict()

    def _rerun(self):
        self.full_fw._rerun()

    def to_db_dict(self):
        return self.full_fw.to_db_dict()

    def __str__(self):
        return 'LazyFireWork object: (id: {})'.format(self.fw_id)

    # Properties that shadow FireWork attributes

    @property
    def tasks(self): return self.partial_fw.tasks

    @tasks.setter
    def tasks(self, value): self.partial_fw.tasks = value

    @property
    def spec(self): return self.partial_fw.spec

    @spec.setter
    def spec(self, value): self.partial_fw.spec = value

    @property
    def name(self): return self.partial_fw.name

    @name.setter
    def name(self, value): self.partial_fw.name = value

    @property
    def created_on(self): return self.partial_fw.created_on

    @created_on.setter
    def created_on(self, value): self.partial_fw.created_on = value

    @property
    def updated_on(self): return self.partial_fw.updated_on

    @updated_on.setter
    def updated_on(self, value): self.partial_fw.updated_on = value

    @property
    def parents(self): return self.partial_fw.parents

    @parents.setter
    def parents(self, value): self.partial_fw.parents = value

    # Properties that shadow FireWork attributes, but which are
    # fetched individually from the DB (i.e. launch objects)

    @property
    def launches(self):
        return self._get_launch_data('launches')

    @launches.setter
    def launches(self, value):
        self._launches['launches'] = True
        self.partial_fw.launches = value

    @property
    def archived_launches(self):
        return self._get_launch_data('archived_launches')

    @archived_launches.setter
    def archived_launches(self, value):
        self._launches['archived_launches'] = True
        self.partial_fw.archived_launches = value

    # Lazy properties that idempotently instantiate a FireWork object
    @property
    def partial_fw(self):
        if not self._fw:
            fields = list(self.db_fields) + list(self.db_launch_fields)
            data = self._fwc.find_one({'fw_id': self.fw_id}, projection=fields)
            launch_data = {}  # move some data to separate launch dict
            for key in self.db_launch_fields:
                launch_data[key] = data[key]
                del data[key]

            self._lids = launch_data
            self._fw = Firework.from_dict(data)
        return self._fw

    @property
    def full_fw(self):
        #map(self._get_launch_data, self.db_launch_fields)
        for launch_field in self.db_launch_fields:
            self._get_launch_data(launch_field)
        return self._fw

    # Get a type of Launch object

    def _get_launch_data(self, name):
        """Pull launch data individually for each field.

        :param name: Name of field, e.g. 'archived_launches'.
        :return: Launch obj (also propagated to self._fw)
        """
        fw = self.partial_fw  # assure stage 1
        if not self._launches[name]:
            launch_ids = self._lids[name]
            if launch_ids:
                data = self._lc.find({'launch_id': {"$in": launch_ids}})
                result = list(map(Launch.from_dict, data))
            else:
                result = []
            setattr(fw, name, result)  # put into real FireWork obj
            self._launches[name] = True
        return getattr(fw, name)
