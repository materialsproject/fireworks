#!/usr/bin/env python

"""
This module contains some of the most central FireWorks classes:

- A FireTaskBase defines the contract for tasks that run within a FireWork (FireTasks)
- A FWAction encapsulates the output of a FireTask and tells FireWorks what to do next after a job completes
- A FireWork defines a workflow step and contains one or more FireTasks.
- A Launch describes the run of a FireWork on a computing resource.
"""
from collections import defaultdict

import datetime
from fireworks.core.fworker import FWorker
from fireworks.utilities.dict_mods import apply_mod
from fireworks.utilities.fw_serializers import FWSerializable, recursive_serialize, recursive_deserialize, serialize_fw
from fireworks.utilities.fw_utilities import get_my_host, get_my_ip

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 5, 2013"


class FireTaskBase(dict, FWSerializable):
    """
    FireTaskBase is used as an abstract class that defines a computing task (FireTask). All FireTasks
    should inherit from FireTaskBase.
    """

    def run_task(self, fw_spec):
        """
        This method gets called when the FireTask is run. It can take in a FireWork spec,
        perform some task using that data, and then return an output in the form of a FWAction.

        :param fw_spec: (dict) a FireWork spec
        :return: (FWAction)
        """
        raise NotImplementedError('The FireTask needs to implement run_task()!')

    @serialize_fw
    @recursive_serialize
    def to_dict(self):
        return dict(self)

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        return cls(m_dict)

    def __getitem__(self, key):
        """
        Reproduce a simple defaultdict-like behavior - any unset parameters return None
        """
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return None


class FWAction(FWSerializable):
    """
    A FWAction encapsulates the output of a FireTask (it is returned by a FireTask after the FireTask completes). The
     FWAction allows a user to store rudimentary output data as well as return commands that alter the workflow.
    """

    def __init__(self, stored_data=None, exit=False, update_spec=None, mod_spec=None, detours=None, additions=None, defuse_children=False, retain_children=False):
        mod_spec = mod_spec if mod_spec is not None else []
        detours = detours if detours is not None else []
        additions = additions if additions is not None else []

        self.stored_data = stored_data if stored_data else {}
        self.exit = exit
        self.update_spec = update_spec
        self.mod_spec = mod_spec if isinstance(mod_spec, list) else [mod_spec]
        self.retain_children = retain_children
        self.detours = detours if isinstance(detours, list) else [detours]
        self.additions = additions if isinstance(additions, list) else [additions]
        self.defuse_children = defuse_children

    @recursive_serialize
    def to_dict(self):
        return {'stored_data': self.stored_data, 'exit': self.exit, 'update_spec': self.update_spec,
                'mod_spec': self.mod_spec, 'detours': self.detours, 'additions': self.additions, 'defuse_children': self.defuse_children, 'retain_children': self.retain_children}

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        d = m_dict
        additions = []
        detours = []
        for f in d['additions']:
            if 'fws' in f:
                additions.append(Workflow.from_dict(f))
            else:
                additions.append(FireWork.from_dict(f))

        for f in d['detours']:
            if 'fws' in f:
                detours.append(Workflow.from_dict(f))
            else:
                detours.append(FireWork.from_dict(f))

        return FWAction(d['stored_data'], d['exit'], d['update_spec'], d['mod_spec'], detours, additions, d['defuse_children'], d['retain_children'])

    @property
    def stop_tasks(self):
        return self.exit or self.update_spec or self.mod_spec or self.detours or self.additions or self.defuse_children


class FireWork(FWSerializable):
    # 'Canceled' is the dominant spelling over 'cancelled' in the US starting around 1985...(Google n-grams)
    STATE_RANKS = {'DEFUSED': 0, 'WAITING': 1, 'READY': 2, 'RESERVED': 3, 'FIZZLED': 4, 'RUNNING': 5, 'CANCELED': 6,
                   'COMPLETED': 7}

    def __init__(self, tasks, spec=None, launches=None, state='WAITING', created_on=None, fw_id=-1):
        """
        :param tasks: (list) a list of FireTasks to run in sequence
        :param spec: (dict) specification of the job to run. Used by the FireTask
        :param fw_id: (int) the FW's database id (negative numbers will be re-assigned dynamically when they are
         entered in the database through the LaunchPad.
        :param launches: (list) a list of Launch objects of this FireWork
        :param state: (str) the state of the FW (e.g. WAITING, RUNNING, COMPLETED, CANCELED)
        """

        # automatically transform tasks into a list, if not in that format
        if not isinstance(tasks, list):
            tasks = [tasks]

        self.tasks = tasks
        self.spec = spec if spec else {}
        self.spec['_tasks'] = [t.to_dict() for t in tasks]  # put tasks in a special location of the spec
        self.fw_id = fw_id
        self.launches = launches if launches else []
        self.created_on = created_on if created_on else datetime.datetime.utcnow()
        self.state = state

    @recursive_serialize
    def to_dict(self):
        m_dict = {'spec': self.spec, 'fw_id': self.fw_id, 'created_on': self.created_on}

        if len(self.launches) > 0:
            m_dict['launches'] = self.launches

        if self.state != 'WAITING':
            m_dict['state'] = self.state

        return m_dict

    def to_db_dict(self):
        m_dict = self.to_dict()
        m_dict['launches'] = [l.launch_id for l in self.launches]  # the launches are stored separately
        m_dict['state'] = self.state
        return m_dict

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        tasks = m_dict['spec']['_tasks']
        l = m_dict.get('launches', None)
        if l:
            l = [Launch.from_dict(tmp) for tmp in l]
        fw_id = m_dict.get('fw_id', -1)
        state = m_dict.get('state', 'WAITING')
        created_on = m_dict.get('created_on', None)

        return FireWork(tasks, m_dict['spec'], l, state, created_on, fw_id)


class Launch(FWSerializable, object):
    def __init__(self, state, launch_dir, fworker=None, host=None, ip=None, action=None, state_history=None,
                 launch_id=None, fw_id=None):
        """
        :param state: (str) the state of the Launch (e.g. RUNNING, COMPLETED)
        :param launch_dir: (str) the directory where the Launch takes place
        :param fworker: (FWorker) The FireWorker running the Launch
        :param host: (str) the hostname where the launch took place (set automatically if None)
        :param ip: (str) the IP address where the launch took place (set automatically if None)
        :param action: (FWAction) the output of the Launch
        :param state_history: (list) a history of all states of the Launch and when they occurred
        :param launch_id: (int) launch_id set by the LaunchPad
        :param fw_id: (int) id of the FireWork this Launch is running
        """

        if state not in FireWork.STATE_RANKS:
            raise ValueError("Invalid launch state: {}".format(state))

        self.fworker = fworker
        self.fw_id = fw_id
        self.host = host if host else get_my_host()
        self.ip = ip if ip else get_my_ip()
        self.launch_dir = launch_dir
        self.action = action if action else None
        self.state_history = state_history if state_history else []
        self.state = state
        self.launch_id = launch_id

    def touch_history(self):
        """
        Updates the update_at field of the state history of a Launch. Used to ping that a Launch is still alive.
        """
        self.state_history[-1]['updated_on'] = datetime.datetime.utcnow()

    def set_reservation_id(self, reservation_id):
        """
        Adds the job_id to the reservation

        :param reservation_id: the id of the reservation (e.g., queue reservation)
        """
        for data in self.state_history:
            if data['state'] == 'RESERVED':
                data['reservation_id'] = reservation_id
                break

    @property
    def state(self):
        """
        :return: (str) The current state of the Launch.
        """
        return self._state

    @state.setter
    def state(self, state):
        """
        Setter the the Launch's state. Automatically trigger an update to state_history when state is changed.

        :param state: (str) the Launch state
        """
        self._state = state
        self._update_state_history(state)

    @property
    def time_start(self):
        """
        :return: (datetime) the time the Launch started RUNNING
        """
        return self._get_time('RUNNING')

    @property
    def time_end(self):
        """
        :return: (datetime) the time the Launch was COMPLETED or FIZZLED
        """
        return self._get_time(['COMPLETED', 'FIZZLED'])

    @property
    def time_reserved(self):
        """
        :return: (datetime) the time the Launch was RESERVED in the queue
        """
        return self._get_time('RESERVED')

    @property
    def last_pinged(self):
        """
        :return: (datetime) the time the Launch last pinged a heartbeat that it was still running
        """
        return self._get_time('RUNNING', True)

    @property
    def runtime_secs(self):
        """
        :return: (int) the number of seconds that the Launch ran for
        """
        start = self.time_start
        end = self.time_end
        if start and end:
            return (end - start).total_seconds()

    @property
    def reservedtime_secs(self):
        """
        :return: (int) number of seconds the Launch was queued
        """
        start = self.time_reserved
        if start:
            end = self.time_start if self.time_start else datetime.datetime.utcnow()
            return (end - start).total_seconds()

    @recursive_serialize
    def to_dict(self):
        return {'fworker': self.fworker, 'fw_id': self.fw_id, 'launch_dir': self.launch_dir, 'host': self.host,
                'ip': self.ip, 'action': self.action, 'state': self.state, 'state_history': self.state_history,
                'launch_id': self.launch_id}

    @recursive_serialize
    def to_db_dict(self):
        m_d = self.to_dict()
        m_d['time_start'] = self.time_start
        m_d['time_end'] = self.time_end
        m_d['runtime_secs'] = self.runtime_secs
        if self.reservedtime_secs:
            m_d['reservedtime_secs'] = self.reservedtime_secs
        return m_d

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        fworker = FWorker.from_dict(m_dict['fworker'])
        action = FWAction.from_dict(m_dict['action']) if m_dict.get('action') else None
        return Launch(m_dict['state'], m_dict['launch_dir'], fworker, m_dict['host'], m_dict['ip'], action,
                      m_dict['state_history'], m_dict['launch_id'], m_dict['fw_id'])

    def _update_state_history(self, state):
        """
        Internal method to update the state history whenever the Launch state is modified

        :param state:
        """
        last_state = self.state_history[-1]['state'] if len(self.state_history) > 0 else None
        if state != last_state:
            now_time = datetime.datetime.utcnow()
            self.state_history.append({'state': state, 'created_on': now_time})
            if state in ['RUNNING', 'RESERVED']:
                self.touch_history()  # add updated_on key

    def _get_time(self, states, use_update_time=False):
        """
        Internal method to help get the time of various events in the Launch (e.g. RUNNING) from the state history

        :param states: match one of these states
        :param use_update_time: use the "updated_on" time rather than "created_on"
        :return: (datetime)
        """
        states = states if isinstance(states, list) else [states]
        for data in self.state_history:
            if data['state'] in states:
                if use_update_time:
                    return data['updated_on']
                return data['created_on']


class Workflow(FWSerializable):
    class Links(dict, FWSerializable):

        @property
        def nodes(self):
            return self.keys()

        @property
        def parent_links(self):
            # note: if performance of parent_links becomes an issue, override delitem/setitem to ensure it's always
            # updated
            d = defaultdict(list)
            for (parent, children) in self.iteritems():
                # add the parents
                for child in children:
                    d[child].append(parent)
            return dict(d)

        def to_dict(self):
            return dict(self)

        def to_db_dict(self):
            # convert to str form for Mongo, which cannot have int keys
            m_dict = {'links': dict([(str(k), list(v)) for (k, v) in self.iteritems()]),
                      'parent_links': dict([(str(k), v) for (k, v) in self.parent_links.iteritems()]),
                      'nodes': self.nodes}
            return m_dict

        @classmethod
        def from_dict(cls, m_dict):
            m_dict = dict([(int(k), list(v)) for (k, v) in m_dict.iteritems()])
            return Workflow.Links(m_dict)

    def __init__(self, fireworks, links_dict=None, metadata=None):

        """
        :param fireworks: a list of FireWork objects
        :param links_dict: A dict representing workflow links
        :param metadata: metadata for this Workflow
        """

        links_dict = links_dict if links_dict else {}

        self.id_fw = {}  # main dict containing mapping of an id to a FireWork object
        for fw in fireworks:
            # check uniqueness, cannot have two FWs with the same id!
            if fw.fw_id in self.id_fw:
                raise ValueError('FW ids must be unique!')
            self.id_fw[fw.fw_id] = fw

            if fw.fw_id not in links_dict:
                links_dict[fw.fw_id] = []

            # transform any non-iterable values to iterables
            for k, v in links_dict.iteritems():
                if not isinstance(v, list):
                    links_dict[k] = [v]

        self.links = Workflow.Links(links_dict)

        # sanity: make sure the set of nodes from the links_dict is equal to the set of nodes from id_fw
        if set(self.links.nodes) != set(self.id_fw.keys()):
            raise ValueError("Specified links don't match given FW")

        self.metadata = metadata if metadata else {}

    @property
    def fws(self):
        return self.id_fw.values()

    def apply_action(self, action, fw_id):
        # TODO: better comment this method
        updated_ids = []

        if action.update_spec:
            for cfid in self.links[fw_id]:
                self.id_fw[cfid].spec.update(action.update_spec)
                updated_ids.append(cfid)

        if action.mod_spec:
            for cfid in self.links[fw_id]:
                for mod in action.mod_spec:
                    apply_mod(mod, self.id_fw[cfid].spec)
                    updated_ids.append(cfid)

        if action.defuse_children:
            for cfid in self.links[fw_id]:
                self.id_fw[cfid].state = 'DEFUSED'
                updated_ids.append(cfid)

        if action.additions:
            for wf in action.additions:
                updated_ids.extend(self._add_wf_to_fw(wf, fw_id, False))

        if action.detours:
            for wf in action.detours:
                updated_ids.extend(self._add_wf_to_fw(wf, fw_id, True))
            if not action.retain_children:
                self.links[fw_id] = []

        return updated_ids

    def _add_wf_to_fw(self, wf, fw_id, detours):
        updated_ids = []

        if isinstance(wf, FireWork):
            wf = Workflow.from_FireWork(wf)

        root_ids = wf.root_fw_ids
        leaf_ids = wf.leaf_fw_ids

        for fw in wf.fws:
            self.id_fw[fw.fw_id] = fw
            if fw.fw_id in leaf_ids and detours:
                self.links[fw.fw_id] = self.links[fw_id]
            elif fw.fw_id in leaf_ids:
                self.links[fw.fw_id] = []
            else:
                self.links[fw.fw_id] = wf.links[fw.fw_id]
            updated_ids.append(fw.fw_id)

        for root_id in root_ids:
            self.links[fw_id].append(root_id)  # add the root id as my child

        return updated_ids

    def refresh(self, fw_id, updated_ids=None):
        updated_ids = updated_ids if updated_ids else set()  # these are the fw_ids to re-enter into the database

        fw = self.id_fw[fw_id]
        prev_state = fw.state

        # if we're defused, just skip altogether
        if fw.state == 'DEFUSED':
            return updated_ids

        # what are the parent states?
        parent_states = [self.id_fw[p].state for p in self.links.parent_links.get(fw_id, [])]

        if len(parent_states) != 0 and not all([s == 'COMPLETED' for s in parent_states]):
            m_state = 'WAITING'

        else:
            # my state depends on launch whose state has the highest 'score' in STATE_RANKS
            max_score = 0
            m_state = 'READY'
            m_action = None

            # TODO: pick the first launch in terms of end date that matches 'COMPLETED'; multiple might exist
            for l in fw.launches:
                if FireWork.STATE_RANKS[l.state] > max_score:
                    max_score = FireWork.STATE_RANKS[l.state]
                    m_state = l.state
                    if m_state == 'COMPLETED':
                        m_action = l.action

        fw.state = m_state

        if m_state != prev_state:
            if m_state == 'COMPLETED':
                updated_ids = updated_ids.union(self.apply_action(m_action, fw.fw_id))

            updated_ids.add(fw_id)
            # refresh all the children
            for child_id in self.links[fw_id]:
                updated_ids = updated_ids.union(self.refresh(child_id, updated_ids))

        return updated_ids

    @property
    def root_fw_ids(self):
        all_ids = set(self.links.nodes)
        child_ids = set(self.links.parent_links.keys())
        root_ids = all_ids.difference(child_ids)
        return list(root_ids)

    @property
    def leaf_fw_ids(self):
        leaves = []
        for id, children in self.links.iteritems():
            if len(children) == 0:
                leaves.append(id)
        return leaves

    def _reassign_ids(self, old_new):
        # update id_fw
        new_id_fw = {}
        for (fwid, fws) in self.id_fw.iteritems():
            new_id_fw[old_new.get(fwid, fwid)] = fws
        self.id_fw = new_id_fw

        # update the Links
        new_l = {}
        for (parent, children) in self.links.iteritems():
            new_parent = old_new.get(parent, parent)
            new_l[new_parent] = [old_new.get(child, child) for child in children]
        self.links = Workflow.Links(new_l)

    def to_dict(self):
        return {'fws': [f.to_dict() for f in self.id_fw.itervalues()], 'links': self.links.to_dict(),
                'metadata': self.metadata}

    def to_db_dict(self):
        m_dict = self.links.to_db_dict()
        m_dict['metadata'] = self.metadata
        return m_dict

    @classmethod
    def from_dict(cls, m_dict):
        return Workflow([FireWork.from_dict(f) for f in m_dict['fws']], Workflow.Links.from_dict(m_dict['links']),
                        m_dict['metadata'])

    @classmethod
    def from_FireWork(cls, fw):
        return Workflow([fw], None)