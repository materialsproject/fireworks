#!/usr/bin/env python

"""
The LaunchPad manages the FireWorks database.
"""
import datetime
from fireworks.core.fw_constants import LAUNCH_RANKS
from fireworks.core.fworker import FWorker
from fireworks.core.rocket import Rocket
from fireworks.core.workflow import Workflow
from fireworks.utilities.fw_serializers import FWSerializable
from pymongo.mongo_client import MongoClient
from fireworks.core.firework import FireWork, Launch
from pymongo import DESCENDING
from fireworks.utilities.dict_mods import apply_mod
from fireworks.utilities.fw_utilities import get_fw_logger

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Jan 30, 2013'

# TODO: add logging throughout
# TODO: probably lots of cleanup is possible
# TODO: be able to un-terminate a FW
# TODO: get children / parents of a FW
# TODO: show a query in the tutorial for get_fw_ids


class LaunchPad(FWSerializable):
    """
    The LaunchPad manages the FireWorks database.
    """

    def __init__(self, host='localhost', port=27017, name='fireworks', username=None, password=None,
                 logdir=None, strm_lvl=None):
        """
        
        :param host:
        :param port:
        :param name:
        :param username:
        :param password:
        :param logdir
        :param strm_lvl
        """
        self.host = host
        self.port = port
        self.name = name
        self.username = username
        self.password = password

        # set up logger
        self.logdir = logdir
        self.strm_lvl = strm_lvl if strm_lvl else 'INFO'
        self.m_logger = get_fw_logger('launchpad', l_dir=self.logdir, stream_level=self.strm_lvl)

        connection = MongoClient(host, port)
        self.database = connection[name]
        if username:
            self.database.authenticate(username, password)

        self.fireworks = self.database.fireworks
        self.launches = self.database.launches
        self.fw_id_assigner = self.database.fw_id_assigner
        self.links = self.database.links

    def to_dict(self):
        """
        Note: usernames/passwords are exported as unencrypted Strings!
        """
        d = {'host': self.host, 'port': self.port, 'name': self.name, 'username': self.username,
             'password': self.password, 'logdir': self.logdir, 'strm_lvl': self.strm_lvl}
        return d

    @classmethod
    def from_dict(cls, d):
        logdir = d.get('logdir', None)
        strm_lvl = d.get('strm_lvl', None)
        return LaunchPad(d['host'], d['port'], d['name'], d['username'], d['password'], logdir, strm_lvl)

    def reset(self, password, require_password=True):
        """
        Create a new FireWorks database. This will overwrite the existing FireWorks database! \
        To safeguard against accidentally erasing an existing database, a password must \
        be entered.
        :param password: A String representing today's date, e.g. '2012-12-31'
        :param require_password: Whether a password is required to reset the DB. Highly \
        recommended to leave this set to True, otherwise you are inviting disaster!
        """
        m_password = datetime.datetime.now().strftime('%Y-%m-%d')

        if password == m_password or not require_password:
            self.fireworks.remove()
            self.launches.remove()
            self.links.remove()
            self._restart_ids(1, 1)
            self._update_indices()
            self.m_logger.info('LaunchPad was RESET.')
        else:
            raise ValueError("Invalid password! Password is today's date: {}".format(m_password))

    def maintain(self):
        self.m_logger.info('Performing maintenance on Launchpad, please wait....')

        self._update_indices()

        self.m_logger.info('LaunchPad was MAINTAINED.')

    def add_wf(self, wf):
        """

        :param wf: a Workflow object.
        """
        if isinstance(wf, FireWork):
            wf = Workflow.from_FireWork(wf)

        # insert the FireWorks and get back mapping of old to new ids
        old_new = self._insert_fws(wf.id_fw.values())

        # redo the Workflow based on new mappings
        wf._reassign_ids(old_new)

        # insert the WFLinks
        self.links.insert(wf.to_db_dict())
        self._refresh_wf(wf.nodes[0])  # wf.nodes[0] is any fw_id in this workflow

        self.m_logger.info('Added a workflow. id_map: {}'.format(old_new))
        return old_new

    def get_launch_by_id(self, launch_id):
        """
        Given a Launch id, return details of the Launch
        :param launch_id: launch id
        :return: Launch object
        """
        return Launch.from_dict(self.launches.find_one(launch_id))

    def get_fw_by_id(self, fw_id):
        """
        Given a FireWork id, give back a FireWork object
        :param fw_id: FireWork id (int)
        :return: FireWork object
        """
        fw_dict = self.fireworks.find_one({'fw_id': fw_id})

        # recreate launches from the launch collection
        launches = []
        for launch_id in fw_dict['launches']:
            launches.append(self.get_launch_by_id(launch_id))
        fw_dict['launches'] = launches

        return FireWork.from_dict(fw_dict)

    def get_fw_ids(self, query=None, sort=False):
        """
        Return all the fw ids that match a query,
        :param query: a dict representing a Mongo query
        """
        fw_ids = []
        criteria = query if query else {}
        sort = [("spec._priority", DESCENDING)] if sort else None
        for fw in self.fireworks.find(criteria, {"fw_id": True}, sort=sort):
            fw_ids.append(fw["fw_id"])

        return fw_ids

    def run_exists(self):
        """
        Checks to see if the database contains any FireWorks that are ready to run
        :return: (T/F)
        """
        return bool(self.fireworks.find_one(self._decorate_query({}), fields={'fw_id': 1}))

    def _update_indices(self):
        self.fireworks.ensure_index('fw_id', unique=True)
        self.fireworks.ensure_index('state')

        self.launches.ensure_index('launch_id', unique=True)
        self.launches.ensure_index('state')
        self.launches.ensure_index('start')
        self.launches.ensure_index('end')
        self.launches.ensure_index('host')
        self.launches.ensure_index('ip')

    def _restart_ids(self, next_fw_id, next_launch_id):
        """
        (internal method) Used to reset id counters

        :param next_fw_id: id to give next FireWork (int)
        :param next_launch_id: id to give next Launch (int)
        """
        self.fw_id_assigner.remove()
        self.fw_id_assigner.insert({"next_fw_id": next_fw_id, "next_launch_id": next_launch_id})
        self.m_logger.debug('RESTARTED fw_id, launch_id to ({}, {})'.format(next_fw_id, next_launch_id))

    def _decorate_query(self, query):
        """
        (internal method) - takes a query and restricts to only those FireWorks that are able to run
        :param query:
        :return:
        """
        query['state'] = {'$in': ['READY', 'FIZZLED']}
        return query

    def _checkout_fw(self, fworker, host, ip, launch_dir):
        """
        (internal method) Finds a FireWork that's ready to be run, marks it as running,
        and returns it to the caller. The caller is responsible for running the FireWork.
        
        :param fworker: A FWorker instance
        :param host: the host making the request (for creating a Launch object)
        :param ip: the ip making the request (for creating a Launch object)
        :param launch_dir: the dir the FW will be run in (for creating a Launch object)
        :return: a FireWork, launch_id tuple
        """
        m_query = self._decorate_query(dict(fworker.query))  # make a copy of the query

        # check out the matching firework, depending on the query set by the FWorker
        m_fw = self.fireworks.find_and_modify(query=m_query, fields={"fw_id": 1}, update={'$set': {'state': 'RUNNING'}},
                                              sort=[("spec._priority", DESCENDING)])
        if not m_fw:
            return None, None
        self.m_logger.debug('Checked out FW with id: {}'.format(m_fw['fw_id']))

        # create a launch
        launch_id = self.get_new_launch_id()
        m_launch = Launch(fworker, host, ip, launch_dir, state='RUNNING', launch_id=launch_id)
        self.launches.insert(m_launch.to_db_dict())
        self.m_logger.debug('Created new Launch with launch_id: {}'.format(launch_id))

        # add launch to FW
        self.fireworks.update(query={'fw_id': m_fw['fw_id']}, update={'$push': {'launches': m_launch.launch_id}})

        # return FW
        return self.get_fw_by_id(m_fw['fw_id']), launch_id

    def _complete_launch(self, launch_id, action=None):
        """
        (internal method) used to mark a FireWork's Launch as completed.
        :param launch_id:
        :param action: the FWAction of what to do next
        """

        # update the launch data to COMPLETED, set end time, etc
        self.launches.update({'launch_id': launch_id}, {'$set': {'state': 'COMPLETED'}})
        self.launches.update({'launch_id': launch_id}, {'$set': {'end': datetime.datetime.utcnow()}})
        self.launches.update({'launch_id': launch_id}, {'$set': {'action': action.to_dict()}})

        # get the wf_dict
        wfc = WFConnections.from_dict(self.links.find_one({'nodes': m_fw.fw_id}))
        # get all the children
        child_fw_ids = wfc.children_links[m_fw.fw_id]

        # depending on the decision, you might have to do additional actions
        if fw_decision.action in ['CONTINUE', 'BREAK']:
            pass
        elif fw_decision.action == 'DEFUSE':
            # mark all children as defused
            for cfid in child_fw_ids:
                self._update_fw_state(cfid, 'DEFUSED')

        elif fw_decision.action == 'MODIFY':
            for cfid in child_fw_ids:
                self._update_fw_spec(cfid, fw_decision.mod_spec['dict_mods'])

        elif fw_decision.action == 'DETOUR':
            # TODO: implement
            raise NotImplementedError('{} action not implemented yet'.format(fw_decision.action))
        elif fw_decision.action == 'ADD':
            old_new = self._insert_fws(fw_decision.mod_spec['add_fws'])
            self._insert_children(m_fw.fw_id, old_new.values())
        elif fw_decision.action == 'ADDIFY':
            # TODO: implement
            raise NotImplementedError('{} action not implemented yet'.format(fw_decision.action))
        elif fw_decision.action == 'PHOENIX':
            # TODO: implement
            raise NotImplementedError('{} action not implemented yet'.format(fw_decision.action))

        self.fireworks.update({"fw_id": m_fw.fw_id}, m_fw.to_db_dict())
        self._refresh_wf(m_fw.fw_id)

    def get_new_fw_id(self):
        """
        Checkout the next FireWork id
        """
        return self.fw_id_assigner.find_and_modify(query={}, update={'$inc': {'next_fw_id': 1}})['next_fw_id']

    def get_new_launch_id(self):
        """
        Checkout the next Launch id
        """
        return self.fw_id_assigner.find_and_modify(query={}, update={'$inc': {'next_launch_id': 1}})['next_launch_id']

    def _insert_fws(self, fws):
        old_new = {} # mapping between old and new FireWork ids
        for fw in fws:
            if not fw.fw_id or fw.fw_id < 0:
                new_id = self.get_new_fw_id()
                old_new[fw.fw_id] = new_id
                fw.fw_id = new_id

            self.fireworks.insert(fw.to_db_dict())

        return old_new

    def _insert_children(self, fw_id, child_ids):
        # TODO: this feels kludgy - we are transforming from dict to Object to dict back to Object back to dict!
        wfc = WFConnections.from_dict(self.links.find_one({'nodes': fw_id}))
        wfc_dict = wfc.to_dict()
        if fw_id in wfc_dict:
            wfc_dict['children_links'][fw_id].extend(child_ids)
        else:
            wfc_dict['children_links'][fw_id] = child_ids

        # TODO: this is a terrible and lazy hack and will bite you later!
        wfc = WFConnections.from_dict(wfc_dict).to_db_dict()
        self.links.update({"nodes": fw_id}, {'$set': {'children_links': wfc['children_links']}})
        self.links.update({"nodes": fw_id}, {'$set': {'parent_links': wfc['parent_links']}})
        self.links.update({"nodes": fw_id}, {'$pushAll': {'nodes': child_ids}})

    def _refresh_wf(self, fw_id):

        """
        Update the FW state of all affected FWs
        :param fw_id:
        """

        # get the workflow containing this fw_id
        wf_dict = self.links.find_one({'nodes': fw_id})

        updated_nodes = set()

        while len(updated_nodes) != len(wf_dict['nodes']):
            for fw_id in wf_dict['nodes']:
                if str(fw_id) not in wf_dict['parent_links']:
                    self._refresh_fw(fw_id, [])
                    updated_nodes.add(fw_id)
                else:
                    # if all parents are updated, update it
                    if all(parent in updated_nodes for parent in wf_dict['parent_links'][str(fw_id)]):
                        self._refresh_fw(fw_id, wf_dict['parent_links'][str(fw_id)])
                        updated_nodes.add(fw_id)

    def _get_fw_state(self, fw_id):
        return self.fireworks.find_one({"fw_id": fw_id}, {"state": True})['state']

    def _update_fw_state(self, fw_id, m_state):
        self.fireworks.update({"fw_id": fw_id}, {"$set": {"state": m_state}})

    def _update_fw_spec(self, fw_id, modder_dicts):
        fw = self.get_fw_by_id(fw_id)

        for mod in modder_dicts:
            apply_mod(mod, fw.spec)

        self.fireworks.update({"fw_id": fw.fw_id}, fw.to_db_dict())

    def _refresh_fw(self, fw_id, parent_ids):
        # if we are defused, just skip this whole thing
        if self._get_fw_state(fw_id) == 'DEFUSED':
            return

        m_state = None

        # what are the parent states?
        parent_states = [self._get_fw_state(p) for p in parent_ids]

        if len(parent_ids) != 0 and not all([s == 'COMPLETED' for s in parent_states]):
            m_state = 'WAITING'

        elif any([s == 'CANCELED' for s in parent_states]):
            m_state = 'CANCELED'

        else:
            # my state depends on launch
            launches = self.get_launches(fw_id)
            max_score = 0
            m_state = 'READY'

            for l in launches:
                if LAUNCH_RANKS[l.state] > max_score:
                    max_score = LAUNCH_RANKS[l.state]
                    m_state = l.state

        self._update_fw_state(fw_id, m_state)

    def get_launches(self, fw_id):
        """
        Given a FireWork id, give back a FireWork object
        :param fw_id: FireWork id (int)
        """
        launches = self.fireworks.find_one({'fw_id': fw_id}, {'launches': 1})['launches']
        return [Launch.from_dict(l) for l in launches]
