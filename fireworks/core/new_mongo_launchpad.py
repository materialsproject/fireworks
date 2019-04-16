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
from fireworks.utilities.fw_serializers import recursive_dict


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


class LaunchPad(FWSerializable):
    """
    The LaunchPad manages the FireWorks database.
    """

    def __init__(self, host=None, port=None, name=None, username=None, password=None,
                 logdir=None, strm_lvl=None, user_indices=None, wf_user_indices=None, ssl=False,
                 ssl_ca_certs=None, ssl_certfile=None, ssl_keyfile=None, ssl_pem_passphrase=None,
                 authsource=None):
        """
        Args:
            host (str): hostname. A MongoDB connection string URI (https://docs.mongodb.com/manual/reference/connection-string/) can be used instead of the remaining options below.
            port (int): port number
            name (str): database name
            username (str)
            password (str)
            logdir (str): path to the log directory
            strm_lvl (str): the logger stream level
            user_indices (list): list of 'fireworks' collection indexes to be built
            wf_user_indices (list): list of 'workflows' collection indexes to be built
            ssl (bool): use TLS/SSL for mongodb connection
            ssl_ca_certs (str): path to the CA certificate to be used for mongodb connection
            ssl_certfile (str): path to the client certificate to be used for mongodb connection
            ssl_keyfile (str): path to the client private key
            ssl_pem_passphrase (str): passphrase for the client private key
            authsource (str): authsource parameter for MongoDB authentication; defaults to "name" (i.e., db name) if not set
        """

        # detect if connection_string mode
        host_uri_mode = False
        if host is not None and (host.startswith("mongodb://") or
                                 host.startswith("mongodb+srv://")):
            host_uri_mode = True

        self.host = host if (host or host_uri_mode) else "localhost"
        self.port = port if (port or host_uri_mode) else 27017
        self.name = name if (name or host_uri_mode) else "fireworks"
        self.username = username
        self.password = password
        self.ssl = ssl
        self.ssl_ca_certs = ssl_ca_certs
        self.ssl_certfile = ssl_certfile
        self.ssl_keyfile = ssl_keyfile
        self.ssl_pem_passphrase = ssl_pem_passphrase
        self.authsource = authsource or self.name

        # set up logger
        self.logdir = logdir
        self.strm_lvl = strm_lvl if strm_lvl else 'INFO'
        self.m_logger = get_fw_logger('launchpad', l_dir=self.logdir, stream_level=self.strm_lvl)

        self.user_indices = user_indices if user_indices else []
        self.wf_user_indices = wf_user_indices if wf_user_indices else []

        # get connection
        if host_uri_mode:
            self.connection = MongoClient(host)
            try:
                option_idx = host.index("?")
                host = host[:option_idx]
            except ValueError:
                pass
            self.db = self.connection[host.split("/")[-1]]
        else:
            self.connection = MongoClient(self.host, self.port, ssl=self.ssl,
                                          ssl_ca_certs=self.ssl_ca_certs,
                                          ssl_certfile=self.ssl_certfile,
                                          ssl_keyfile=self.ssl_keyfile,
                                          ssl_pem_passphrase=self.ssl_pem_passphrase,
                                          socketTimeoutMS=MONGO_SOCKET_TIMEOUT_MS,
                                          username=self.username,
                                          password=self.password,
                                          authSource=self.authsource)
            self.db = self.connection[self.name]

        self.fireworks = self.db.fireworks
        self.launches = self.db.launches
        self.offline_runs = self.db.offline_runs
        self.fw_id_assigner = self.db.fw_id_assigner
        self.workflows = self.db.workflows
        if GRIDFS_FALLBACK_COLLECTION:
            self.gridfs_fallback = gridfs.GridFS(self.db, GRIDFS_FALLBACK_COLLECTION)
        else:
            self.gridfs_fallback = None

        self.backup_launch_data = {}
        self.backup_fw_data = {}

    def to_dict(self):
        """
        Note: usernames/passwords are exported as unencrypted Strings!
        """
        return {
            'host': self.host,
            'port': self.port,
            'name': self.name,
            'username': self.username,
            'password': self.password,
            'logdir': self.logdir,
            'strm_lvl': self.strm_lvl,
            'user_indices': self.user_indices,
            'wf_user_indices': self.wf_user_indices,
            'ssl': self.ssl,
            'ssl_ca_certs': self.ssl_ca_certs,
            'ssl_certfile': self.ssl_certfile,
            'ssl_keyfile': self.ssl_keyfile,
            'ssl_pem_passphrase': self.ssl_pem_passphrase,
            'authsource': self.authsource}

    def update_spec(self, fw_ids, spec_document, mongo=False):
        """
        Update fireworks with a spec. Sometimes you need to modify a firework in progress.

        Args:
            fw_ids [int]: All fw_ids to modify.
            spec_document (dict): The spec document. Note that only modifications to
                the spec key are allowed. So if you supply {"_tasks.1.parameter": "hello"},
                you are effectively modifying spec._tasks.1.parameter in the actual fireworks
                collection.
            mongo (bool): spec_document uses mongo syntax to directly update the spec
        """
        if mongo:
            mod_spec = spec_document
        else:
            mod_spec = {"$set": {("spec." + k): v for k, v in spec_document.items()} }

        allowed_states = ["READY", "WAITING", "FIZZLED", "DEFUSED", "PAUSED"]
        self.fireworks.update_many({'fw_id': {"$in": fw_ids},
                                    'state': {"$in": allowed_states}}, mod_spec)
        for fw in self.fireworks.find({'fw_id': {"$in": fw_ids}, 'state': {"$nin": allowed_states}},
                                      {"fw_id": 1, "state": 1}):
            self.m_logger.warning("Cannot update spec of fw_id: {} with state: {}. "
                               "Try rerunning first".format(fw['fw_id'], fw['state']))

    @classmethod
    def from_dict(cls, d):
        port = d.get('port', None)
        name = d.get('name', None)
        username = d.get('username', None)
        password = d.get('password', None)
        logdir = d.get('logdir', None)
        strm_lvl = d.get('strm_lvl', None)
        user_indices = d.get('user_indices', [])
        wf_user_indices = d.get('wf_user_indices', [])
        ssl = d.get('ssl', False)
        ssl_ca_certs = d.get('ssl_ca_certs', d.get('ssl_ca_file', None))  # ssl_ca_file was the old notation for FWS < 1.5.5
        ssl_certfile = d.get('ssl_certfile', None)
        ssl_keyfile = d.get('ssl_keyfile', None)
        ssl_pem_passphrase = d.get('ssl_pem_passphrase', None)
        authsource= d.get('authsource', None)
        return LaunchPad(d['host'], port, name, username, password,
                         logdir, strm_lvl, user_indices, wf_user_indices, ssl,
                         ssl_ca_certs, ssl_certfile, ssl_keyfile, ssl_pem_passphrase,
                         authsource)

    def _reset(self):
        self.fireworks.delete_many({})
        self.launches.delete_many({})
        self.workflows.delete_many({})
        #self.offline_runs.delete_many({})
        self._restart_ids(1)
        if self.gridfs_fallback is not None:
            self.db.drop_collection("{}.chunks".format(GRIDFS_FALLBACK_COLLECTION))
            self.db.drop_collection("{}.files".format(GRIDFS_FALLBACK_COLLECTION))
        self.tuneup()
        self.m_logger.info('LaunchPad was RESET.')

    def _get_launch_by_id(self, launch_id):
        """
        Given a Launch id, return launch info.

        Args:
            launch_id (int): launch id

        Returns:
            dict
        """
        m_launch = self.launches.find_one({'launch_id': launch_id})
        if m_launch:
            m_launch["action"] = get_action_from_gridfs(m_launch.get("action"), self.gridfs_fallback)
            if 'launch_id' in m_launch:
                m_launch.pop('launch_id')
            return m_launch
        raise ValueError('No Launch exists with launch_id: {}'.format(launch_id))

    def _get_launch_by_fw_id(self, fw_id, launch_idx=None):
        """
        Given a Firework id, return launches.

        Args:
            launch_id (int): launch id

        Returns:
            dict
        """
        if launch_idx == None:
            m_launches = self.launches.find({'fw_id': fw_id})
            if m_launches:
                for i, m_launch in enumerate(m_launches):
                    m_launch["action"] = get_action_from_gridfs(m_launch.get("action"),
                                                                self.gridfs_fallback)
                    if 'launch_id' in m_launch:
                        m_launch.pop('launch_id')
                    m_launch['launch_idx'] = i
                return m_launches
        else:
            launch_ids = self.launches.find({'fw_id': fw_id}, projection={'launch_id': 1},
                                            sort={'launch_id': ASCENDING})
            launch_id = launch_ids[launch_idx]
            launch = self.launches.find_one({'launch_id': launch_id})
            launch['launch_idx'] = launch_idx if launch_idx >= 0\
                                   else len(launch_ids)+launch_idx
            if 'launch_id' in launch:
                launch.pop('launch_id')
            launch["action"] = get_action_from_gridfs(launch.get("action"),
                                                      self.gridfs_fallback)
            return launch
        raise ValueError('No Launch exists with launch_id: {}'.format(launch_id))

    def get_fw_dict_by_id(self, fw_id, launch_idx=-1):
        """
        Given firework id, return firework dict.

        Args:
            fw_id (int): firework id

        Returns:
            dict
        """
        fw_dict = self.fireworks.find_one({'fw_id': fw_id})    

        if not fw_dict:
            raise ValueError('No Firework exists with id: {}'.format(fw_id))

        if fw_dict["STATE"] not in ["WAITING", "READY", "RESERVED"]:
            launch = self._get_launch_by_fw_id(fw_id, launch_idx)
        else:
            launch = Firework._new_launch()

        fw_dict['launch'] = launch
        fw_dict.pop('launches')
        return fw_dict

    def _delete_wf(self, fw_id, fw_ids):
        # TODO COME BACK TO THIS
        potential_launches = []
        launch_ids = []
        for i in fw_ids:
            launches = self._get_launch_by_fw_id(i)
            potential_launches += [l['launch_id'] for l in launches]

        for i in potential_launches:  # only remove launches if no other fws refer to them
            if not self.fireworks.find_one({'$or': [{"launches": i}, {'archived_launches': i}],
                                            'fw_id': {"$nin": fw_ids}}, {'launch_id': 1}):
                launch_ids.append(i)

        if self.gridfs_fallback is not None:
            for lid in launch_ids:
                for f in self.gridfs_fallback.find({"metadata.launch_id": lid}):
                    self.gridfs_fallback.delete(f._id)
        self.launches.delete_many({'launch_id': {"$in": launch_ids}})
        self.offline_runs.delete_many({'launch_id': {"$in": launch_ids}})
        self.fireworks.delete_many({"fw_id": {"$in": fw_ids}})
        self.workflows.delete_one({'nodes': fw_id})

    def _get_all_launch_dirs(self, fw_ids):
        pass
        """
        if delete_launch_dirs:
            launch_dirs = []
            for i in launch_ids:
                launch_dirs.append(self.launches.find_one({'launch_id': i}, {'launch_dir': 1})['launch_dir'])
            print("Remove folders %s" % launch_dirs)
            for d in launch_dirs:
                shutil.rmtree(d, ignore_errors=True)
        """

    def _get_wf_data(self, wf_id, mode='more'):
        # THIS OVERRIDES A DEFAULT _get_wf_data
        wf_fields = ["state", "created_on", "name", "nodes"]
        fw_fields = ["state", "fw_id"]
        launch_fields = []

        if mode != "less":
            wf_fields.append("updated_on")
            fw_fields.extend(["name", "launches"])
            launch_fields.append("launch_idx")
            launch_fields.append("launch_dir")

        if mode == "reservations":
            launch_fields.append("state_history.reservation_id")

        if mode == "all":
            wf_fields = None

        wf = self.workflows.find_one({"nodes": fw_id}, projection=wf_fields)
        fw_data = []
        id_name_map = {}
        launch_ids = []
        for fw in self.fireworks.find({"fw_id": {"$in": wf["nodes"]}}, projection=fw_fields):
            if launch_fields:
                launch_ids.extend(fw["launches"])
            fw_data.append(fw)
            if mode != "less":
                id_name_map[fw["fw_id"]] = "%s--%d" % (fw["name"], fw["fw_id"])

        if launch_fields:
            launch_info = defaultdict(list)
            for l in self.launches.find({'launch_id': {"$in": launch_ids}}, projection=launch_fields):
                for i, fw in enumerate(fw_data):
                    if l["launch_id"] in fw["launches"]:
                        launch_info[i].append(l)
            for k, v in launch_info.items():
                fw_data[k]["launches"] = v

        wf["fw"] = fw_data
        return wf

    def get_fw_ids(self, query=None, sort=None, limit=0, count_only=False):
        """
        Return all the fw ids that match a query.

        Args:
            query (dict): representing a Mongo query
            sort [(str,str)]: sort argument in Pymongo format
            limit (int): limit the results
            count_only (bool): only return the count rather than explicit ids
            launches_mode (bool): query the launches collection instead of fireworks

        Returns:
            list: list of firework ids matching the query
        """
        fw_ids = []
        coll = "fireworks"
        criteria = query if query else {}

        if count_only:
            if limit:
                return ValueError("Cannot count_only and limit at the same time!")
            return getattr(self, coll).find(criteria, {}, sort=sort).count()

        for fw in getattr(self, coll).find(criteria, {"fw_id": True}, sort=sort).limit(limit):
            fw_ids.append(fw["fw_id"])
        return fw_ids

    def get_wf_ids(self, query=None, sort=None, limit=0, count_only=False):
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
        wf_ids = []
        criteria = query if query else {}
        if count_only:
            return self.workflows.find(criteria, {"nodes": True}, sort=sort).limit(limit).count()

        for fw in self.workflows.find(criteria, {"nodes": True}, sort=sort).limit(limit):
            wf_ids.append(fw["nodes"][0])

        return wf_ids

    def tuneup(self, bkground=True):
        """
        Database tuneup: build indexes
        """
        self.m_logger.info('Performing db tune-up')

        self.m_logger.debug('Updating indices...')
        self.fireworks.create_index('fw_id', unique=True, background=bkground)
        for f in ("state", 'spec._category', 'created_on', 'updated_on' 'name', 'launches'):
            self.fireworks.create_index(f, background=bkground)

        self.launches.create_index('launch_id', unique=True, background=bkground)
        self.launches.create_index('fw_id', background=bkground)
        self.launches.create_index('state_history.reservation_id', background=bkground)

        if GRIDFS_FALLBACK_COLLECTION is not None:
            files_collection = self.db["{}.files".format(GRIDFS_FALLBACK_COLLECTION)]
            files_collection.create_index('metadata.launch_id', unique=True, background=bkground)

        for f in ('state', 'time_start', 'time_end', 'host', 'ip', 'fworker.name'):
            self.launches.create_index(f, background=bkground)

        for f in ('name', 'created_on', 'updated_on', 'nodes'):
            self.workflows.create_index(f, background=bkground)

        for idx in self.user_indices:
            self.fireworks.create_index(idx, background=bkground)

        for idx in self.wf_user_indices:
            self.workflows.create_index(idx, background=bkground)

        # for frontend, which needs to sort on _id after querying on state
        self.fireworks.create_index([("state", DESCENDING), ("_id", DESCENDING)], background=bkground)
        self.fireworks.create_index([("state", DESCENDING), ("spec._priority", DESCENDING),
                                     ("created_on", DESCENDING)], background=bkground)
        self.fireworks.create_index([("state", DESCENDING), ("spec._priority", DESCENDING),
                                     ("created_on", ASCENDING)], background=bkground)
        self.workflows.create_index([("state", DESCENDING), ("_id", DESCENDING)], background=bkground)

        if not bkground:
            self.m_logger.debug('Compacting database...')
            try:
                self.db.command({'compact': 'fireworks'})
                self.db.command({'compact': 'launches'})
            except:
                self.m_logger.debug('Database compaction failed (not critical)')

    def _restart_ids(self, next_fw_id, next_launch_id):
        """
        internal method used to reset firework id counters.

        Args:
            next_fw_id (int): id to give next Firework
            next_launch_id (int): id to give next Launch
        """
        self.fw_id_assigner.delete_many({})
        self.fw_id_assigner.find_one_and_replace({'_id': -1},
                                                 {'next_fw_id': next_fw_id,
                                                  'next_launch_id': next_launch_id}, upsert=True)
        self.m_logger.debug(
            'RESTARTED fw_id, launch_id to ({}, {})'.format(next_fw_id, next_launch_id))

    def _get_a_fw_to_run(self, query=None, fw_id=None, launch_idx=-1, checkout=True):
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
        m_query = dict(query) if query else {}  # make a defensive copy
        m_query['state'] = 'READY'
        sortby = [("spec._priority", DESCENDING)]

        if SORT_FWS.upper() == "FIFO":
            sortby.append(("created_on", ASCENDING))
        elif SORT_FWS.upper() == "FILO":
            sortby.append(("created_on", DESCENDING))

        # Override query if fw_id defined
        if fw_id:
            m_query = {"fw_id": fw_id, "state": {'$in': ['READY', 'RESERVED']}}

        while True:
            # check out the matching firework, depending on the query set by the FWorker
            if checkout:
                m_fw = self.fireworks.find_one_and_update(m_query,
                                                          {'$set': {'state': 'RESERVED',
                                                           'updated_on': datetime.datetime.utcnow()}},
                                                          sort=sortby)
            else:
                m_fw = self.fireworks.find_one(m_query, {'fw_id': 1, 'spec': 1}, sort=sortby)

            if not m_fw:
                return None
            m_fw = self.get_fw_by_id(m_fw['fw_id'])
            if self._check_fw_for_uniqueness(m_fw):
                return m_fw

    def _get_active_launch_ids(self):
        """
        Get all the launch ids.

        Returns:
            list: all launch ids
        """
        all_launch_ids = []
        for l in self.fireworks.find({}, {"launches": 1}):
            all_launch_ids.extend(l['launches'])
        return all_launch_ids

    def _get_fw_ids_from_reservation_id(self, reservation_id):
        """
        Given the reservation id, return the list of firework ids.

        Args:
            reservation_id (int)

        Returns:
            [int]: list of firework ids.
        """
        fw_ids = []
        ld = self.launches.find_one({"state_history.reservation_id": reservation_id},
                                      {'launch_id': 1})
        for fw in self.fireworks.find({'fw_id': ld['fw_id'],
                                        'launches': ld['launch_id']}, {'fw_id': 1}):
            fw_ids.append(fw['fw_id'])
        return fw_ids

    def _replace_fw(self, m_fw, state=None, upsert=False, fw_id=None):
        """
        Update a Firework m_fw in the database by replacing it.
        If upsert is True, add a new firework/launch if the no
        firework/launch has the same id
        """
        query = {'fw_id': fw_id or m_fw.fw_id}
        if type(state) == list:
            state = {'$in': state}
        if state:
            query['state'] = state
        fw_dict = m_fw.to_db_dict()
        launch = fw_dict.pop['launch']
        
        launch_ids = self.fireworks.find(query, projection={'launches': 1})['launches']
        if m_fw.launch_idx >= len(launch_ids):
            launch['launch_id'] = self.get_new_launch_id()
            launch_ids.append(launch['launch_id'])
        else:
            launch['launch_id'] = launch_ids[m_fw.launch_idx]
        fw_dict['launches'] = launch_ids
        fw = self.fireworks.find_one_and_replace(query, fw_dict, upsert=upsert)
        query = {'launch_id': launch['launch_id']}
        self.launches.find_one_and_replace(query, launch, upsert=upsert)

    def _get_fw_ids_from_reservation_id(self, reservation_id):
        fw_ids = []
        l_id = self.launches.find_one({"state_history.reservation_id": reservation_id},
                                  {'launch_id': 1})['launch_id']
        for fw in self.fireworks.find({'launches': l_id}, {'fw_id': 1}):
            fw_ids.append(fw['fw_id'])
        return fw_ids

    def _get_next_launch_idx(fw_id):
        return len(self.fireworks.find_one({'fw_id': fw_id}, projection=['launches'])['launches'])

    def _find_timeout_fws(self, state, expiration_secs, query=None):
        now_time = datetime.datetime.utcnow()
        cutoff_timestr = (now_time - datetime.timedelta(seconds=expiration_secs)).isoformat()
        lostruns_query = {'state': state,
                          'state_history':
                              {'$elemMatch':
                                   {'state': state,
                                    'updated_on': {'$lte': cutoff_timestr}
                                    }
                               }
                          }

        if query:
            fw_ids = [x["fw_id"] for x in self.fireworks.find(query,
                                                          {"fw_id": 1})]
            lostruns_query["fw_id"] = {"$in": fw_ids}

        fw_ids = self.launches.find(lostruns_query, {'fw_id': 1})
        return list(set([id_dict['fw_id'] for id_dict in fw_ids]))

    """
    def _launch_fw(m_fw, reserved_fw):
        # This function does any database access/edit that requires knowing
        # reserved_fw.
        m_launch = m_fw.launch
        r_launch = None
        if reserved_fw:
            r_launch = self.launches.find_one({'launch_id': reserved_fw.launch_idx,
                                                'fw_id': reserved_fw.fw_id})
        lid = self.get_new_launch_id() if (r_launch is None)\
                                else r_launch['launch_id']
        # insert the launch (upsert->add regardless of whether launch_id already exists)
        self.launches.find_one_and_replace({'launch_id': lid},
                                           m_launch, upsert=True)
        self.m_logger.debug('Created/updated Launch with launch_id: {}'.format(launch_id))
        self.backup_launch_data[m_launch['launch_id']] = m_launch
    """

    def _get_lazy_firework(self, fw_id):
        return LazyFirework(fw_id, self.fireworks, self.launches, self.gridfs_fallback)

    def _find_wf(self, fw_id, projection=None, sort=None):
        return self.workflows.find_one({'nodes': fw_id}, projection=projection, sort=sort)

    def _checkin_fw(self, m_fw, action=None, state='COMPLETED'):
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
        m_launch = m_fw.launch

        try:
            self.launches.find_one_and_replace({'launch_id': m_launch['launch_id']},
                                               m_launch, upsert=True)
        except DocumentTooLarge as err:
            launch_db_dict = m_launch
            action_dict = launch_db_dict.get("action", None)
            if not action_dict:
                # in case the action is empty and it is not the source of
                # the error, raise the exception again.
                raise
            if self.gridfs_fallback is None:
                err.args = (err.args[0]
                            + '. Set GRIDFS_FALLBACK_COLLECTION in FW_config.yaml'
                              ' to a value different from None',)
                raise err

            # encoding required for python2/3 compatibility.
            action_id = self.gridfs_fallback.put(json.dumps(action_dict), encoding="utf-8",
                                                 metadata={"launch_id": launch_id})
            launch_db_dict["action"] = {"gridfs_id": str(action_id)}
            self.m_logger.warning("The size of the launch document was too large. Saving "
                               "the action in gridfs.")

            self.launches.find_one_and_replace({'launch_id': m_launch['launch_id']},
                                               launch_db_dict, upsert=True)


        # find all the fws that have this launch
        for fw in self.fireworks.find({'launch_id': m_launch['launch_id']}, {'fw_id': 1}):
            fw_id = fw['fw_id']
            self._refresh_wf(fw_id)

        # change return type to dict to make return type serializable to support job packing
        return m_launch

    def _update_fw(self, m_fw, state=None, allowed_states=None, launch_idx=-1,
                    touch_history=True, checkpoint=None):
        # need to refine structure of launch_idx/launch_id arg to get correct id
        if type(m_fw) == int:
            m_fw = self.get_fw_by_id(m_fw, launch_idx)
        reset_launch = STATE_RANKS[state] > STATE_RANKS[m_fw.state]\
                        and state in ['WAITING, READY, RESERVED']
        if touch_history:
            if reset_launch:
                m_fw.reset_launch(launch_idx=self._get_next_launch_idx(fw_id))
            m_fw.state = state
        query_dict = {'fw_id': m_fw.fw_id, 'launch_id': m_fw.launch['launch_id']}
        if type(allowed_states) == list:
            state = {'$in': state}
        if allowed_states is not None:
            query_dict['state'] = allowed_states
        launch = m_fw.launch
        command_dict_launch = {'$set': {'state_history': launch['state_history'],
                                 'trackers': [t.to_dict() for t in launch['trackers']]}}
                                 # maybe remove to_dict() above?
        command_dict_fw = {}
        if state is not None:
            command_dict['$set']['state'] = state
            command_dict['$set']['updated_on'] = m_fw.updated_on
        if not reset_launch:
            self.fireworks.update_one(query_dict, command_dict_fw)
            self.launches.update_one(query_dict, command_dict_launch)
        else:
            # make a new fw and a new launch by upserting with a new launch_idx
            #self._replace_fw(m_fw, upsert=True)
            self.fireworks.update_one(query_dict, command_dict_fw)
        return m_fw

    def get_new_fw_id(self, quantity=1):
        """
        Checkout the next Firework id

        Args:
            quantity (int): optionally ask for many ids, otherwise defaults to 1
                            this then returns the *first* fw_id in that range
        """
        try:
            return self.fw_id_assigner.find_one_and_update({}, {'$inc': {'next_fw_id': quantity}})['next_fw_id']
        except:
            raise ValueError("Could not get next FW id! If you have not yet initialized the database,"
                             " please do so by performing a database reset (e.g., lpad reset)")

    def get_new_launch_id(self):
        """
        Checkout the next Launch id
        """
        try:
            return self.fw_id_assigner.find_one_and_update({}, {'$inc': {'next_launch_id': 1}})['next_launch_id']
        except:
            raise ValueError("Could not get next launch id! If you have not yet initialized the "
                             "database, please do so by performing a database reset (e.g., lpad reset)")

    def _find_fws(self, fw_id=None, launch_sort=-1, allowed_states=None,
                    projection=None, sort=None, m_query=None):
        query_dict = {}
        if fw_id is not None:
            if type(fw_id) == list:
                fw_id = {'$in': fw_id}
            query_dict['fw_id':] = fw_id
        if not (allowed_states is None):
            if type(allowed_states) == str:
                query_dict['state'] = {allowed_states}
            else:
                query_dict['state'] = {'$in': [allowed_states]}
        if not (m_query is None):
            query_dict.update(m_query)
        fws = self.fireworks.find(query_dict,
                                    projection=projection, sort=sort)
        sort['launch_id'] = launch_sort
        all_fws = []
        for fw in fws:
            query_dict = {'launch_id': {'$in': fw['launches']}}
            launches = self.launches.find(query_dict, sort=sort)
            query_dict['state'] = fw['state']
            if self.launches.count(query_dict) == 0:
                new_fw = dict(fw)
                new_fw['launch'] = _new_launch()
                all_fws.append(new_fw)
                #raise ValueError('FW has no launch data!')
            for launch in launches:
                new_fw = dict(fw)
                new_fw['launch'] = launch
                all_fws.append(new_fw)
        return all_fws

    def rerun_fw(self, fw_id, rerun_duplicates=True, recover_launch=None, recover_mode=None):
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
            f = self.fireworks.find_one({"fw_id": fw_id, "spec._dupefinder": {"$exists": True}},
                                        {'launches':1})
            if f:
                for d in self.fireworks.find({"launches": {"$in": f['launches']},
                                              "fw_id": {"$ne": fw_id}}, {"fw_id": 1}):
                    duplicates.append(d['fw_id'])
            duplicates = list(set(duplicates))

        # Launch recovery
        if recover_launch is not None:
            recovery = self.get_recovery(fw_id, recover_launch)
            recovery.update({'_mode': recover_mode})
            set_spec = recursive_dict({'$set': {'spec._recovery': recovery}})
            if recover_mode == 'prev_dir':
                prev_dir = self.get_launch_by_id(recovery.get('_launch_id')).launch_dir
                set_spec['$set']['spec._launch_dir'] = prev_dir
            self.fireworks.find_one_and_update({"fw_id": fw_id}, set_spec)

        # If no launch recovery specified, unset the firework recovery spec
        else:
            set_spec = {"$unset":{"spec._recovery":""}}
            self.fireworks.find_one_and_update({"fw_id":fw_id}, set_spec)


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

    def get_recovery(self, fw_id, launch_id='last'):
        """
        function to get recovery data for a given fw and launch
        Args:
            fw_id (int): fw id to get recovery data for
            launch_id (int or 'last'): launch_id to get recovery data for, if 'last'
                recovery data is generated from last launch
        """
        m_fw = self.get_fw_by_id(fw_id)
        if launch_id == 'last':
            launch = m_fw.launches[-1]
        else:
            launch = self.get_launch_by_id(launch_id)
        recovery = launch.state_history[-1].get("checkpoint")
        recovery.update({'_prev_dir': launch.launch_dir,
                         '_launch_id': launch.launch_id})
        return recovery

    def _internal_fizzle(self, fw_id, launch_idx=-1):
        self.fireworks.find_one_and_update({"fw_id": fw_id},
                                            {"$set": {"state": "FIZZLED"}},
                                            sort={'launch_idx': DESCENDING})
        self.workflows.find_one_and_update({"nodes": fw_id}, {"$set": {"state": "FIZZLED",\
                                           "fw_states.{}".format(fw_id): "FIZZLED"}})

    def _insert_fws(self, fws):
        if type(fws) == FireWork:
            
        else:
            self.fireworks.insert_many(fw.to_db_dict() for fw in fws)

    def _delete_fws(self, fw_ids):
        

    def _replace_fws(self, fw_ids, fws):
        self.fireworks.delete_many({'fw_id': {'$in': fw_ids}})
        if type(fws) == FireWork:
            fw_dict = fw.to_db_dict()
            launch = fw_dict.pop('launch')
            self.fireworks.insert_one(fw_dict)
            self.fireworks.insert_one(fw.to_db_dict())
        else:
            self.fireworks.insert_many(fw.to_db_dict() for fw in fws)


    def _update_wf(self, wf, updated_ids):
        """
        Update the workflow with the update firework ids.
        Note: must be called within an enclosing WFLock

        Args:
            wf (Workflow)
            updated_ids ([int]): list of firework ids
        """
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
        # redo the links and fw_states
        wf = wf.to_db_dict()
        wf['locked'] = True  # preserve the lock!
        self.workflows.find_one_and_replace({'nodes': query_node}, wf)

    def _steal_launches(self, thief_fw):
        """
        Check if there are duplicates. If there are duplicates, the matching firework's launches
        are added to the launches of the given firework.

        Returns:
             bool: False if the given firework is unique
        """
        stolen = False
        if thief_fw.state in ['READY', 'RESERVED'] and '_dupefinder' in thief_fw.spec:
            m_dupefinder = thief_fw.spec['_dupefinder']
            # get the query that will limit the number of results to check as duplicates
            m_query = m_dupefinder.query(thief_fw.to_dict()["spec"])
            self.m_logger.debug('Querying for duplicates, fw_id: {}'.format(thief_fw.fw_id))
            # iterate through all potential duplicates in the DB
            for potential_match in self.fireworks.find(m_query):
                self.m_logger.debug('Verifying for duplicates, fw_ids: {}, {}'.format(
                    thief_fw.fw_id, potential_match['fw_id']))

                # see if verification is needed, as this slows the process
                verified = False
                try:
                    m_dupefinder.verify({}, {})  # is implemented test

                except NotImplementedError:
                    verified = True  # no dupefinder.verify() implemented, skip verification

                except:  # we want to catch any exceptions from testing an empty dict, which the dupefinder might not be designed for
                    pass

                if not verified:
                    # dupefinder.verify() is implemented, let's call verify()
                    spec1 = dict(thief_fw.to_dict()['spec'])  # defensive copy
                    spec2 = dict(potential_match['spec'])  # defensive copy
                    verified = m_dupefinder.verify(spec1, spec2)

                if verified:
                    # steal the launches
                    victim_fw = self.get_fw_by_id(potential_match['fw_id'])
                    thief_launches = [l.launch_id for l in thief_fw.launches]
                    valuable_launches = [l for l in victim_fw.launches if l.launch_id not in thief_launches]
                    for launch in valuable_launches:
                        thief_fw.launches.append(launch)
                        stolen = True
                        self.m_logger.info('Duplicate found! fwids {} and {}'.format(
                            thief_fw.fw_id, potential_match['fw_id']))
        return stolen

    def set_priority(self, fw_id, priority):
        """
        Set priority to the firework with the given id.

        Args:
            fw_id (int): firework id
            priority
        """
        self.fireworks.find_one_and_update({"fw_id": fw_id}, {'$set': {'spec._priority': priority}})

    def add_offline_run(self, launch_id, fw_id, name):
        """
        Add the launch and firework to the offline_run collection.

        Args:
            launch_id (int): launch id
            fw_id (id): firework id
            name (str)
        """
        d = {'fw_id': fw_id}
        d['launch_id'] = launch_id
        d['name'] = name
        d['created_on'] = datetime.datetime.utcnow().isoformat()
        d['updated_on'] = datetime.datetime.utcnow().isoformat()
        d['deprecated'] = False
        d['completed'] = False
        self.offline_runs.insert_one(d)

    def recover_offline(self, launch_id, ignore_errors=False, print_errors=False):
        """
        Update the launch state using the offline data in FW_offline.json file.

        Args:
            launch_id (int): launch id
            ignore_errors (bool)
            print_errors (bool)

        Returns:
            firework id if the recovering fails otherwise None
        """
        # get the launch directory
        m_launch = self.get_launch_by_id(launch_id)
        try:
            self.m_logger.debug("RECOVERING fw_id: {}".format(m_launch.fw_id))
            # look for ping file - update the Firework if this is the case
            ping_loc = os.path.join(m_launch.launch_dir, "FW_ping.json")
            if os.path.exists(ping_loc):
                ping_dict = loadfn(ping_loc)
                self.ping_launch(launch_id, ptime=ping_dict['ping_time'])

            # look for action in FW_offline.json
            offline_loc = zpath(os.path.join(m_launch.launch_dir,
                                             "FW_offline.json"))
            with zopen(offline_loc) as f:
                offline_data = loadfn(offline_loc)
                if 'started_on' in offline_data:
                    m_launch.state = 'RUNNING'
                    for s in m_launch.state_history:
                        if s['state'] == 'RUNNING':
                            s['created_on'] = reconstitute_dates(offline_data['started_on'])
                    l = self.launches.find_one_and_replace({'launch_id': m_launch.launch_id},
                                                           m_launch.to_db_dict(), upsert=True)
                    fw_id = l['fw_id']
                    f = self.fireworks.find_one_and_update({'fw_id': fw_id},
                                                           {'$set':
                                                                {'state': 'RUNNING',
                                                                 'updated_on': datetime.datetime.utcnow()
                                                                 }
                                                            })
                    if f:
                        self._refresh_wf(fw_id)

                if 'checkpoint' in offline_data:
                    m_launch.touch_history(checkpoint=offline_data['checkpoint'])
                    self.launches.find_one_and_replace({'launch_id': m_launch.launch_id},
                                                       m_launch.to_db_dict(), upsert=True)

                if 'fwaction' in offline_data:
                    fwaction = FWAction.from_dict(offline_data['fwaction'])
                    state = offline_data['state']
                    m_launch = Launch.from_dict(
                        self.complete_launch(launch_id, fwaction, state))
                    for s in m_launch.state_history:
                        if s['state'] == offline_data['state']:
                            s['created_on'] = reconstitute_dates(offline_data['completed_on'])
                    self.launches.find_one_and_update({'launch_id': m_launch.launch_id},
                                                      {'$set':
                                                           {'state_history': m_launch.state_history}
                                                      })
                    self.offline_runs.update_one({"launch_id": launch_id},
                                                 {"$set": {"completed": True}})

            # update the updated_on
            self.offline_runs.update_one({"launch_id": launch_id},
                                         {"$set": {"updated_on": datetime.datetime.utcnow().isoformat()}})
            return None
        except:
            if print_errors:
                self.m_logger.error("failed recovering launch_id {}.\n{}".format(
                    launch_id, traceback.format_exc()))
            if not ignore_errors:
                traceback.print_exc()
                m_action = FWAction(stored_data={'_message': 'runtime error during task',
                                                 '_task': None,
                                                 '_exception': {'_stacktrace': traceback.format_exc(),
                                                                '_details': None}},
                                    exit=True)
                self.complete_launch(launch_id, m_action, 'FIZZLED')
                self.offline_runs.update_one({"launch_id": launch_id}, {"$set": {"completed": True}})
            return m_launch.fw_id

    def forget_offline(self, launchid_or_fwid, launch_mode=True):
        """
        Unmark the offline run for the given launch or firework id.

        Args:
            launchid_or_fwid (int): launch od or firework id
            launch_mode (bool): if True then launch id is given.
        """
        q = {"launch_id": launchid_or_fwid} if launch_mode else {"fw_id": launchid_or_fwid}
        self.offline_runs.update_many(q, {"$set": {"deprecated": True}})

    def log_message(self, level, message):
        """
        Support for job packing

        Args:
            level (str)
            message (str)
        """
        self.m_logger.log(level, message)


class LazyFirework(object):
    """
    A LazyFirework only has the fw_id, and retrieves other data just-in-time.
    This representation can speed up Workflow loading as only "important" FWs need to be
    fully loaded.
    """

    # Get these fields from DB when creating new FireWork object
    db_fields = ('name', 'fw_id', 'spec', 'created_on', 'state')
    db_launch_fields = ('launches', 'archived_launches')

    def __init__(self, fw_id, fw_coll, launch_coll, fallback_fs):
        """
        Args:
            fw_id (int): firework id
            fw_coll (pymongo.collection): fireworks collection
            launch_coll (pymongo.collection): launches collection
        """
        # This is the only attribute known w/o a DB query
        self.fw_id = fw_id
        self._fwc, self._lc, self._ffs = fw_coll, launch_coll, fallback_fs
        self._launches = {k: False for k in self.db_launch_fields}
        self._fw, self._lids, self._state = None, None, None

    # FireWork methods

    # Treat state as special case as it is always required when accessing a Firework lazily
    # If the partial fw is not available the state is fetched independently
    @property
    def state(self):
        if self._fw is not None:
            self._state = self._fw.state
        elif self._state is None:
            self._state = self._fwc.find_one({'fw_id': self.fw_id}, projection=['state'])['state']
        return self._state

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
    def tasks(self):
        return self.partial_fw.tasks

    @tasks.setter
    def tasks(self, value):
        self.partial_fw.tasks = value

    @property
    def spec(self):
        return self.partial_fw.spec

    @spec.setter
    def spec(self, value):
        self.partial_fw.spec = value

    @property
    def name(self):
        return self.partial_fw.name

    @name.setter
    def name(self, value):
        self.partial_fw.name = value

    @property
    def created_on(self):
        return self.partial_fw.created_on

    @created_on.setter
    def created_on(self, value):
        self.partial_fw.created_on = value

    @property
    def updated_on(self):
        return self.partial_fw.updated_on

    @updated_on.setter
    def updated_on(self, value):
        self.partial_fw.updated_on = value

    @property
    def parents(self):
        if self._fw is not None:
            return self.partial_fw.parents
        else:
            return []

    @parents.setter
    def parents(self, value):
        self.partial_fw.parents = value

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
        """
        Pull launch data individually for each field.

        Args:
            name (str): Name of field, e.g. 'archived_launches'.

        Returns:
            Launch obj (also propagated to self._fw)
        """
        fw = self.partial_fw  # assure stage 1
        if not self._launches[name]:
            launch_ids = self._lids[name]
            result = []
            if launch_ids:
                data = self._lc.find({'launch_id': {"$in": launch_ids}})
                for ld in data:
                    ld["action"] = get_action_from_gridfs(ld.get("action"), self._ffs)
                    result.append(Launch.from_dict(ld))

            setattr(fw, name, result)  # put into real FireWork obj
            self._launches[name] = True
        return getattr(fw, name)


def get_action_from_gridfs(action_dict, fallback_fs):
    """
    Helper function to obtain the correct dictionary of the FWAction associated
    with a launch. If necessary retrieves the information from gridfs based
    on its identifier, otherwise simply returns the dictionary in input.
    Should be used when accessing a launch to ensure the presence of the
    correct action dictionary.
    
    Args:
        action_dict (dict): the dictionary contained in the "action" key of a launch
            document.
        fallback_fs (GridFS): the GridFS with the actions exceeding the 16MB limit.
    Returns:
        dict: the dictionary of the action.
    """

    if not action_dict or "gridfs_id" not in action_dict:
        return action_dict

    action_gridfs_id = ObjectId(action_dict["gridfs_id"])

    action_data = fallback_fs.get(ObjectId(action_gridfs_id))
    return json.loads(action_data.read())