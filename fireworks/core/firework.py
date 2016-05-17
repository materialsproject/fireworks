# coding: utf-8

from __future__ import unicode_literals
from monty.dev import deprecated

"""
This module contains some of the most central FireWorks classes:


- A Workflow is a sequence of FireWorks as a DAG (directed acyclic graph)
- A Firework defines a workflow step and contains one or more FireTasks along
 with its Launches.
- A Launch describes the run of a Firework on a computing resource.
- A FireTaskBase defines the contract for tasks that run within a Firework (
FireTasks)
- A FWAction encapsulates the output of a FireTask and tells FireWorks what
to do next after a job completes
"""

from collections import defaultdict, OrderedDict
import abc
from datetime import datetime
import os
import pprint

from monty.io import reverse_readline, zopen
from monty.os.path import zpath
from six import add_metaclass

from fireworks.fw_config import TRACKER_LINES, NEGATIVE_FWID_CTR, EXCEPT_DETAILS_ON_RERUN
from fireworks.core.fworker import FWorker
from fireworks.utilities.dict_mods import apply_mod
from fireworks.utilities.fw_serializers import FWSerializable, \
    recursive_serialize, recursive_deserialize, serialize_fw
from fireworks.utilities.fw_utilities import get_my_host, get_my_ip, NestedClassGetter


__author__ = "Anubhav Jain"
__credits__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 5, 2013"



class FireTaskMeta(abc.ABCMeta):

    def __call__(cls, *args, **kwargs):
        o = abc.ABCMeta.__call__(cls, *args, **kwargs)
        for k in cls.required_params:
            if k not in o:
                raise ValueError("Required parameter {} not specified!"
                                 .format(k))
        return o


@add_metaclass(FireTaskMeta)
class FireTaskBase(defaultdict, FWSerializable):
    """
    FireTaskBase is used like an abstract class that defines a computing task
    (FireTask). All FireTasks should inherit from FireTaskBase.

    You can set parameters of a FireTask like you'd use a dict.
    """

    # Specify required parameters with class variable. Consistency will be
    # checked upon init.
    required_params = []

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    @abc.abstractmethod
    def run_task(self, fw_spec):
        """
        This method gets called when the FireTask is run. It can take in a
        Firework spec, perform some task using that data, and then return an
        output in the form of a FWAction.

        Args:
            fw_spec (dict): A Firework spec. This comes from the master spec.
                In addition, this spec contains a special "_fw_env" key that
                contains the env settings of the FWorker calling this method.
                This provides for abstracting out certain commands or
                settings. For example, "foo" may be named "foo1" in resource
                1 and "foo2" in resource 2. The FWorker env can specify {
                "foo": "foo1"}, which maps an abstract variable "foo" to the
                relevant "foo1" or "foo2". You can then write a task that
                uses fw_spec["_fw_env"]["foo"] that will work across all
                these multiple resources.

        Returns:
            (FWAction)
        """
        raise NotImplementedError("You must have a run_task implemented!")

    @serialize_fw
    @recursive_serialize
    def to_dict(self):
        return dict(self)

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        return cls(m_dict)

    def __repr__(self):
        return '<{}>:{}'.format(self.fw_name, dict(self))


class FWAction(FWSerializable):
    """
    A FWAction encapsulates the output of a FireTask (it is returned by a
    FireTask after the FireTask completes). The
     FWAction allows a user to store rudimentary output data as well as
     return commands that alter the workflow.
    """

    def __init__(self, stored_data=None, exit=False, update_spec=None,
                 mod_spec=None, additions=None, detours=None,
                 defuse_children=False, defuse_workflow=False):
        """
        :param stored_data: (dict) data to store from the run. Does not
        affect the operation of FireWorks.
        :param exit: (bool) if set to True, any remaining FireTasks within
        the same Firework are skipped.
        :param update_spec: (dict) specifies how to update the child FW's spec
        :param mod_spec: ([dict]) update the child FW's spec using the
        DictMod language (more flexible than update_spec)
        :param additions: ([Workflow]) a list of WFs/FWs to add as children
        :param detours: ([Workflow]) a list of WFs/FWs to add as children (
        they will inherit the current FW's children)
        :param defuse_children: (bool) defuse all the original children of
        this Firework
        :param defuse_workflow: (bool) defuse all incomplete steps of this workflow
        """
        mod_spec = mod_spec if mod_spec is not None else []
        additions = additions if additions is not None else []
        detours = detours if detours is not None else []

        self.stored_data = stored_data if stored_data else {}
        self.exit = exit
        self.update_spec = update_spec if update_spec else {}
        self.mod_spec = mod_spec if isinstance(mod_spec, (list, tuple)) else [mod_spec]
        self.additions = additions if isinstance(additions, (list, tuple)) else [
            additions]
        self.detours = detours if isinstance(detours, (list, tuple)) else [detours]
        self.defuse_children = defuse_children
        self.defuse_workflow = defuse_workflow

    @recursive_serialize
    def to_dict(self):
        return {'stored_data': self.stored_data, 'exit': self.exit,
                'update_spec': self.update_spec,
                'mod_spec': self.mod_spec, 'additions': self.additions,
                'detours': self.detours,
                'defuse_children': self.defuse_children,
                'defuse_workflow': self.defuse_workflow}

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        d = m_dict
        additions = [Workflow.from_dict(f) for f in d['additions']]
        detours = [Workflow.from_dict(f) for f in d['detours']]
        return FWAction(d['stored_data'], d['exit'], d['update_spec'],
                        d['mod_spec'], additions, detours,
                        d['defuse_children'], d.get('defuse_workflow', False))

    @property
    def skip_remaining_tasks(self):
        """
        If the FWAction gives any dynamic action, we skip the subsequent
        FireTasks

        :return: (bool)
        """
        return self.exit or self.detours or self.additions or self.defuse_children or self.defuse_workflow

    def __str__(self):
        return "FWAction\n" + pprint.pformat(self.to_dict())


class Firework(FWSerializable):
    """
    A Firework is a workflow step and might be contain several FireTasks.
    """

    STATE_RANKS = {'ARCHIVED': -2, 'FIZZLED': -1, 'DEFUSED': 0, 'WAITING': 1, 'READY': 2,
                   'RESERVED': 3, 'RUNNING': 4, 'COMPLETED': 5}

    # note: if you modify this signature, you must also modify LazyFirework
    def __init__(self, tasks, spec=None, name=None, launches=None,
                 archived_launches=None, state='WAITING', created_on=None,
                 fw_id=None, parents=None, updated_on=None):
        """
        :param tasks: ([FireTask]) a list of FireTasks to run in sequence
        :param spec: (dict) specification of the job to run. Used by the
        FireTask
        :param launches: ([Launch]) a list of Launch objects of this Firework
        :param archived_launches: ([Launch]) a list of archived Launch
        objects of this Firework
        :param state: (str) the state of the FW (e.g. WAITING, RUNNING,
        COMPLETED, ARCHIVED)
        :param created_on: (datetime) - time of creation
        :param fw_id: (int) an identification number for this Firework
        :param parents: (Firework or [Firework]) list of parent FWs this FW depends on
        :param updated_on: (datetime) - last time the STATE was updated
        """

        tasks = tasks if isinstance(tasks, (list, tuple)) else [tasks]

        self.tasks = tasks
        self.spec = spec.copy() if spec else {}
        self.spec['_tasks'] = [t.to_dict() for t in
                               tasks]  # put tasks in a special location of the spec

        self.name = name or 'Unnamed FW'  # do it this way to prevent None
        # names
        if fw_id is not None:
            self.fw_id = fw_id
        else:
            global NEGATIVE_FWID_CTR
            NEGATIVE_FWID_CTR -= 1
            self.fw_id = NEGATIVE_FWID_CTR

        self.launches = launches if launches else []
        self.archived_launches = archived_launches if archived_launches else []
        self.created_on = created_on or datetime.utcnow()
        self.updated_on = updated_on or datetime.utcnow()

        parents = [parents] if isinstance(parents, Firework) else parents
        self.parents = parents if parents else []

        self._state = state

    @property
    def state(self):
        """
        :return: (str) The current state of the Firework
        """
        return self._state

    @state.setter
    def state(self, state):
        """
        Setter for the the FW state, which triggers updated_on change

        :param state: (str) the state to set for the FW
        """
        self._state = state
        self.updated_on = datetime.utcnow()

    @recursive_serialize
    def to_dict(self):
        m_dict = {'spec': self.spec, 'fw_id': self.fw_id,
                  'created_on': self.created_on, 'updated_on': self.updated_on}

        # only serialize these fields if non-empty
        if len(list(self.launches)) > 0:
            m_dict['launches'] = self.launches

        if len(list(self.archived_launches)) > 0:
            m_dict['archived_launches'] = self.archived_launches

        # keep export of new FWs to files clean
        if self.state != 'WAITING':
            m_dict['state'] = self.state

        m_dict['name'] = self.name

        return m_dict

    def _rerun(self):
        """
        Moves all Launches to archived Launches and resets the state to
        'WAITING'. The Firework can thus be re-run \
        even if it was Launched in the past. This method should be called by
        a Workflow because a refresh is needed \
        after calling this method.

        """
        if self.state == 'FIZZLED':
            last_launch = self.launches[-1]
            if (EXCEPT_DETAILS_ON_RERUN and last_launch.action and
                last_launch.action.stored_data.get('_exception', {}).get('_details')):
                # add the exception details to the spec
                self.spec['_exception_details'] = last_launch.action.stored_data['_exception']['_details']
            else:
                # clean spec from stale details
                self.spec.pop('_exception_details', None)

        self.archived_launches.extend(self.launches)
        self.archived_launches = list(set(self.archived_launches))  # filter duplicates
        self.launches = []
        self.state = 'WAITING'

    def to_db_dict(self):
        m_dict = self.to_dict()
        m_dict['launches'] = [l.launch_id for l in
                              self.launches]  # the launches are stored
        # separately
        m_dict['archived_launches'] = [l.launch_id for l in
                                       self.archived_launches]  # the
        # archived launches are stored separately
        m_dict['state'] = self.state
        return m_dict

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        tasks = m_dict['spec']['_tasks']
        launches = [Launch.from_dict(tmp) for tmp in m_dict.get('launches', [])]
        archived_launches = [Launch.from_dict(tmp) for tmp in
                             m_dict.get('archived_launches', [])]
        fw_id = m_dict.get('fw_id', -1)
        state = m_dict.get('state', 'WAITING')
        created_on = m_dict.get('created_on')
        updated_on = m_dict.get('updated_on')
        name = m_dict.get('name', None)

        return Firework(tasks, m_dict['spec'], name, launches, archived_launches,
                        state, created_on, fw_id, updated_on=updated_on)

    def __str__(self):
        return 'Firework object: (id: %i , name: %s)' % (self.fw_id, self.fw_name)

class Tracker(FWSerializable, object):
    """
    A Tracker monitors a file and returns the last N lines for updating the Launch object
    """

    MAX_TRACKER_LINES = 1000

    def __init__(self, filename, nlines=TRACKER_LINES, content='', allow_zipped=False):
        if nlines > self.MAX_TRACKER_LINES:
            raise ValueError("Tracker only supports a maximum of {} lines; you put {}.".format(
                self.MAX_TRACKER_LINES, nlines))
        self.filename = filename
        self.nlines = nlines
        self.content = content
        self.allow_zipped = allow_zipped

    def track_file(self, launch_dir=None):
        """
        Reads the monitored file and returns back the last N lines
        :param launch_dir: directory where job was launched in case of relative filename
        :return:
        """
        m_file = self.filename
        if launch_dir and not os.path.isabs(self.filename):
            m_file = os.path.join(launch_dir, m_file)

        lines = []
        if self.allow_zipped:
            m_file = zpath(m_file)

        if os.path.exists(m_file):
            with zopen(m_file) as f:
                for l in reverse_readline(f):
                    lines.append(l)
                    if len(lines) == self.nlines:
                        break
            self.content = '\n'.join(reversed(lines))

        return self.content

    def to_dict(self):
        m_dict = {'filename': self.filename, 'nlines': self.nlines,
                  'allow_zipped': self.allow_zipped}
        if self.content:
            m_dict['content'] = self.content
        return m_dict

    @classmethod
    def from_dict(cls, m_dict):
        return Tracker(m_dict['filename'], m_dict['nlines'],
                       m_dict.get('content', ''), m_dict.get('allow_zipped', False))

    def __str__(self):
        return '### Filename: {}\n{}'.format(self.filename, self.content)


class Launch(FWSerializable, object):
    """
    A Launch encapsulates data about a specific run of a Firework on a
    computing resource
    """

    def __init__(self, state, launch_dir, fworker=None, host=None, ip=None,
                 trackers=None, action=None, state_history=None,
                 launch_id=None, fw_id=None):
        """
        :param state: (str) the state of the Launch (e.g. RUNNING, COMPLETED)
        :param launch_dir: (str) the directory where the Launch takes place
        :param fworker: (FWorker) The FireWorker running the Launch
        :param host: (str) the hostname where the launch took place (set
        automatically if None)
        :param ip: (str) the IP address where the launch took place (set
        automatically if None)
        :param trackers: ([Tracker]) File Trackers for this Launch
        :param action: (FWAction) the output of the Launch
        :param state_history: ([dict]) a history of all states of the Launch
        and when they occurred
        :param launch_id: (int) launch_id set by the LaunchPad
        :param fw_id: (int) id of the Firework this Launch is running
        """

        if state not in Firework.STATE_RANKS:
            raise ValueError("Invalid launch state: {}".format(state))

        self.launch_dir = launch_dir
        self.fworker = fworker or FWorker()
        self.host = host or get_my_host()
        self.ip = ip or get_my_ip()
        self.trackers = trackers if trackers else []
        self.action = action if action else None
        self.state_history = state_history if state_history else []
        self.state = state
        self.launch_id = launch_id
        self.fw_id = fw_id

    def touch_history(self, update_time=None):
        """
        Updates the update_at field of the state history of a Launch. Used to
         ping that a Launch is still alive.
        """
        update_time = update_time or datetime.utcnow()
        self.state_history[-1]['updated_on'] = update_time

    def set_reservation_id(self, reservation_id):
        """
        Adds the job_id to the reservation

        :param reservation_id: (str) the id of the reservation (e.g.,
        queue reservation)
        """
        for data in self.state_history:
            if data['state'] == 'RESERVED' and 'reservation_id' not in data:
                data['reservation_id'] = str(reservation_id)
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
        Setter for the the Launch's state. Automatically triggers an update
        to state_history.

        :param state: (str) the state to set for the Launch
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
        :return: (datetime) the time the Launch last pinged a heartbeat that
        it was still running
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
        :return: (int) number of seconds the Launch was stuck as RESERVED in
        a queue
        """
        start = self.time_reserved
        if start:
            end = self.time_start if self.time_start else datetime \
                .utcnow()
            return (end - start).total_seconds()

    @recursive_serialize
    def to_dict(self):
        return {'fworker': self.fworker, 'fw_id': self.fw_id,
                'launch_dir': self.launch_dir, 'host': self.host,
                'ip': self.ip, 'trackers': self.trackers,
                'action': self.action, 'state': self.state,
                'state_history': self.state_history,
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
        fworker = FWorker.from_dict(m_dict['fworker']) if m_dict['fworker'] else None
        action = FWAction.from_dict(m_dict['action']) if m_dict.get(
            'action') else None
        trackers = [Tracker.from_dict(f) for f in m_dict['trackers']] if m_dict.get(
            'trackers') else None
        return Launch(m_dict['state'], m_dict['launch_dir'], fworker,
                      m_dict['host'], m_dict['ip'], trackers, action,
                      m_dict['state_history'], m_dict['launch_id'],
                      m_dict['fw_id'])

    def _update_state_history(self, state):
        """
        Internal method to update the state history whenever the Launch state
         is modified

        :param state:
        """
        last_state = self.state_history[-1]['state'] if len(
            self.state_history) > 0 else None
        if state != last_state:
            now_time = datetime.utcnow()
            self.state_history.append({'state': state, 'created_on': now_time})
            if state in ['RUNNING', 'RESERVED']:
                self.touch_history()  # add updated_on key

    def _get_time(self, states, use_update_time=False):
        """
        Internal method to help get the time of various events in the Launch
        (e.g. RUNNING) from the state history

        :param states: match one of these states
        :param use_update_time: use the "updated_on" time rather than
        "created_on"
        :return: (datetime)
        """
        states = states if isinstance(states, (list, tuple)) else [states]
        for data in self.state_history:
            if data['state'] in states:
                if use_update_time:
                    return data['updated_on']
                return data['created_on']


class Workflow(FWSerializable):
    """
    A Workflow connects a group of FireWorks in an execution order
    """

    class Links(dict, FWSerializable):
        """
        An inner class for storing the DAG links between FireWorks
        """

        def __init__(self, *args, **kwargs):
            super(Workflow.Links, self).__init__(*args, **kwargs)

            for k, v in list(self.items()):
                if not isinstance(v, (list, tuple)):
                    self[k] = [v]  # v must be list

                self[k] = [x.fw_id if hasattr(x, "fw_id") else x for x in self[k]]

                if not isinstance(k, int):
                    if hasattr(k, "fw_id"):  # maybe it's a String?
                        self[k.fw_id] = self[k]
                    else:  # maybe it's a String?
                        try:
                            self[int(k)] = self[k]  # k must be int
                        except:
                            pass  # garbage input
                    del self[k]

        @property
        def nodes(self):
            allnodes = list(self.keys())
            for v in self.values():
                allnodes.extend(v)
            return list(set(allnodes))

        @property
        def parent_links(self):
            # note: if performance of parent_links becomes an issue,
            # override delitem/setitem to update parent_links
            child_parents = defaultdict(list)
            for (parent, children) in self.items():
                for child in children:
                    child_parents[child].append(parent)
            return dict(child_parents)

        def to_dict(self):
            # convert to str form for Mongo, which cannot have int keys
            return dict([(str(k), v) for (k, v) in self.items()])

        def to_db_dict(self):
            # convert to str form for Mongo, which cannot have int keys
            m_dict = {
                'links': dict([(str(k), v) for (k, v) in self.items()]),
                'parent_links': dict(
                    [(str(k), v) for (k, v) in self.parent_links.items()]),
                'nodes': self.nodes}
            return m_dict

        @classmethod
        def from_dict(cls, m_dict):
            return Workflow.Links(m_dict)

        def __setstate__(self, state):
            for k, v in state:
                self[k] = v

        def __reduce__(self):
            # to support Pickling of inner classes (for multi-job launcher's multiprocessing)
            # return a class which can return this class when called with the
            # appropriate tuple of arguments
            state = list(self.items())
            return (NestedClassGetter(),
                    (Workflow, self.__class__.__name__, ),
                    state)

    def __init__(self, fireworks, links_dict=None, name=None, metadata=None, created_on=None,
                 updated_on=None, fw_states=None):
        """
        :param fireworks: ([Firework]) - all FireWorks in this workflow
        :param links_dict: (dict) links between the FWs as (parent_id):[(
        child_id1, child_id2)]
        :param name: (str) naem of workflow
        :param metadata: (dict) metadata for this Workflow
        :param created_on: (datetime)
        :param updated_on: (datetime)
        :param fw_states: (dict) - leave alone unless you are purposefully creating a Lazy-style WF
        """
        name = name or 'unnamed WF'  # prevent None names

        links_dict = links_dict if links_dict else {}

        self.id_fw = {}  # main dict containing mapping of an id to a
        # Firework object
        for fw in fireworks:
            if fw.fw_id in self.id_fw:
                raise ValueError('FW ids must be unique!')
            self.id_fw[fw.fw_id] = fw

            if fw.fw_id not in links_dict and fw not in links_dict:
                links_dict[fw.fw_id] = []

        self.links = Workflow.Links(links_dict)

        # add depends on
        for fw in fireworks:
            for pfw in fw.parents:
                if pfw.fw_id not in self.links:
                    raise ValueError(
                        "FW_id: {} defines a dependent link to FW_id: {}, but the latter was not added to the workflow!".format(
                            fw.fw_id, pfw.fw_id))
                if fw.fw_id not in self.links[pfw.fw_id]:
                    self.links[pfw.fw_id].append(fw.fw_id)

        self.name = name

        # sanity: make sure the set of nodes from the links_dict is equal to
        # the set of nodes from id_fw
        if set(self.links.nodes) != set(map(int, self.id_fw.keys())):
            raise ValueError("Specified links don't match given FW")

        self.metadata = metadata if metadata else {}
        self.created_on = created_on or datetime.utcnow()
        self.updated_on = updated_on or datetime.utcnow()

        # Dict containing mapping of an id to a firework state. The states are stored locally and redundantly for speed purpose
        if fw_states:
            self.fw_states = fw_states
        else:
            self.fw_states = {key:self.id_fw[key].state for key in self.id_fw}

    @property
    def fws(self):
        return list(self.id_fw.values())

    @property
    def state(self):

        # get state of workflow
        m_state = 'READY'
        #states = [fw.state for fw in self.fws]
        states = self.fw_states.values()
        leaf_states = [self.fw_states[fw_id] for fw_id in self.leaf_fw_ids]
        if all([s == 'COMPLETED' for s in leaf_states]):
            m_state = 'COMPLETED'
        elif all([s == 'ARCHIVED' for s in states]):
            m_state = 'ARCHIVED'
        elif any([s == 'DEFUSED' for s in states]):
            m_state = 'DEFUSED'
        elif any([s == 'FIZZLED' for s in states]):
            # When _allow_fizzled_parents is set for some fireworks, the workflow is running if a given fizzled
            # firework has all its childs COMPLETED, RUNNING, RESERVED or READY.
            # For each fizzled fw, we thus have to check the states of their children
            fizzled_ids = [fw_id for fw_id, state in self.fw_states.items() if state not in ['READY', 'RUNNING',
                                                                                             'COMPLETED', 'RESERVED']]
            for fizzled_id in fizzled_ids:
                # If a fizzled fw is a leaf fw, then the workflow is fizzled
                if fizzled_id in self.leaf_fw_ids:
                    m_state = 'FIZZLED'
                    break
                childs_ids = self.links[fizzled_id]
                mybreak = False
                for child_id in childs_ids:
                    # If one of the childs of a fizzled fw is also fizzled, then the workflow is fizzled
                    # WARNING: this does not handle the case in which the childs of this child might be not fizzled
                    #          one would need some recursive check here, but we can assume that _allow_fizzled_parents
                    #          is usually not set twice in a row (in a child as well as in a "grandchild" of a given
                    #          fw). Anyway, if in the end the workflow reaches completion, its state will be COMPLETED
                    #          as it will be set as such by the first check on COMPLETED states of all leaf fireworks.
                    if self.fw_states[child_id] == 'FIZZLED':
                        mybreak = True
                        m_state = 'FIZZLED'
                        break
                if mybreak:
                    break
            else:
                m_state = 'RUNNING'
        elif any([s == 'COMPLETED' for s in states]) or any([s == 'RUNNING' for s in states]):
            m_state = 'RUNNING'
        elif any([s == 'RESERVED' for s in states]):
            m_state = 'RESERVED'

        return m_state

    def apply_action(self, action, fw_id):
        """
        Apply a FWAction on a Firework in the Workflow

        :param action: (FWAction) action to apply
        :param fw_id: (int) id of Firework on which to apply the action
        :return: ([int]) list of Firework ids that were updated or new
        """

        updated_ids = []

        # update the spec of the children FireWorks
        if action.update_spec:
            for cfid in self.links[fw_id]:
                self.id_fw[cfid].spec.update(action.update_spec)
                updated_ids.append(cfid)

        # update the spec of the children FireWorks using DictMod language
        if action.mod_spec:
            for cfid in self.links[fw_id]:
                for mod in action.mod_spec:
                    apply_mod(mod, self.id_fw[cfid].spec)
                    updated_ids.append(cfid)

        # defuse children
        if action.defuse_children:
            for cfid in self.links[fw_id]:
                self.id_fw[cfid].state = 'DEFUSED'
                updated_ids.append(cfid)

        # defuse workflow
        if action.defuse_workflow:
            for fw_id in self.links.nodes:
                if self.id_fw[fw_id].state not in ['FIZZLED', 'COMPLETED']:
                    self.id_fw[fw_id].state = 'DEFUSED'
                    updated_ids.append(fw_id)

        # add detour FireWorks
        # this should be done *before* additions
        if action.detours:
            for wf in action.detours:
                new_updates = self.append_wf(wf, [fw_id], detour=True, pull_spec_mods=False)
                if len(set(updated_ids).intersection(new_updates)) > 0:
                    raise ValueError(
                        "Cannot use duplicated fw_ids when dynamically detouring workflows!")
                updated_ids.extend(new_updates)

        # add additional FireWorks
        if action.additions:
            for wf in action.additions:
                new_updates = self.append_wf(wf, [fw_id], detour=False, pull_spec_mods=False)
                if len(set(updated_ids).intersection(new_updates)) > 0:
                    raise ValueError(
                        "Cannot use duplicated fw_ids when dynamically adding workflows!")
                updated_ids.extend(new_updates)

        return list(set(updated_ids))

    def rerun_fw(self, fw_id, updated_ids=None):
        """
        Archives the launches of a Firework so that it can be re-run.
        :param fw_id: (int)
        :return: ([int]) list of Firework ids that were updated
        """

        updated_ids = updated_ids if updated_ids else set()
        m_fw = self.id_fw[fw_id]
        m_fw._rerun()
        updated_ids.add(fw_id)

        # re-run all the children
        for child_id in self.links[fw_id]:
            updated_ids = updated_ids.union(
                self.rerun_fw(child_id, updated_ids))

        # refresh the WF to get the states updated
        return self.refresh(fw_id, updated_ids)

    def append_wf(self, new_wf, fw_ids, detour=False, pull_spec_mods=False):
        """
        Method to add a workflow as a child to a Firework
        Note: detours must have children that have STATE_RANK that is WAITING or below

        :param new_wf: (Workflow) New Workflow to add
        :param fw_ids: ([int]) ids of the parent Fireworks on which to add the Workflow
        :param detour: (bool) add children of the current Firework to the Workflow's leaves
        :param pull_spec_mods: (bool) pull spec mods of COMPLETED parents, refreshes the WF states.
        :return: ([int]) list of Firework ids that were updated or new
        """
        updated_ids = []

        root_ids = new_wf.root_fw_ids
        leaf_ids = new_wf.leaf_fw_ids

        # make sure detour runs do not link to ready/running/completed/etc. runs
        if detour:
            for fw_id in fw_ids:
                if fw_id in self.links:
                    # make sure all of these links are WAITING, else the DETOUR is not well defined
                    ready_run = [(f >= 0 and Firework.STATE_RANKS[self.fw_states[f]] > 1) for f in self.links[fw_id]]
                    if any(ready_run):
                        raise ValueError("fw_id: {}: Detour option only works if all children of detours are not READY to run and have not already run".format(fw_id))

        # make sure all new child fws have negative fw_id
        for new_fw in new_wf.fws:
            if new_fw.fw_id >= 0:  # note - this is also used later in the 'detour' code
                raise ValueError(
                    'FireWorks to add must use a negative fw_id! Got fw_id: '
                    '{}'.format(
                        new_fw.fw_id))

        # completed checks - go ahead and append
        for new_fw in new_wf.fws:
            self.id_fw[new_fw.fw_id] = new_fw  # add new_fw to id_fw

            if new_fw.fw_id in leaf_ids:
                if detour:
                    for fw_id in fw_ids:
                        self.links[new_fw.fw_id] = [f for f in self.links[fw_id] if f >= 0]  # add children of current FW to new FW
                else:
                    self.links[new_fw.fw_id] = []
            else:
                self.links[new_fw.fw_id] = new_wf.links[new_fw.fw_id]
            updated_ids.append(new_fw.fw_id)

        for fw_id in fw_ids:
            for root_id in root_ids:
                self.links[fw_id].append(root_id)  # add the root id as my child

                if pull_spec_mods:  # re-apply some actions of the parent
                    m_fw = self.id_fw[fw_id]  # get the parent FW
                    m_launch = self._get_representative_launch(m_fw)  # get Launch of parent
                    if m_launch:
                        # pull spec update
                        if m_launch.state == 'COMPLETED' and m_launch.action.update_spec:
                            new_wf.id_fw[root_id].spec.update(m_launch.action.update_spec)
                        # pull spec mods
                        if m_launch.state == 'COMPLETED' and m_launch.action.mod_spec:
                            for mod in m_launch.action.mod_spec:
                                apply_mod(mod, new_wf.id_fw[root_id].spec)

        for new_fw in new_wf.fws:
            updated_ids = self.refresh(new_fw.fw_id, set(updated_ids))

        return updated_ids

    def refresh(self, fw_id, updated_ids=None):
        """
        Refreshes the state of a Firework and any affected children.

        :param fw_id: (int) id of the Firework on which to perform the refresh
        :param updated_ids: ([int])
        :return: (set(int)) list of Firework ids that were updated
        """

        updated_ids = updated_ids if updated_ids else set()  # these are the
        # fw_ids to re-enter into the database

        fw = self.id_fw[fw_id]
        prev_state = fw.state

        # if we're defused or archived, just skip altogether
        if fw.state == 'DEFUSED' or fw.state == 'ARCHIVED':
            self.fw_states[fw_id] = fw.state
            return updated_ids

        # what are the parent states?
        parent_states = [self.id_fw[p].state for p in
                         self.links.parent_links.get(fw_id, [])]

        completed_parent_states = ['COMPLETED']
        if fw.spec.get('_allow_fizzled_parents'):
            completed_parent_states.append('FIZZLED')

        if len(parent_states) != 0 and not all(s in completed_parent_states for s in parent_states):
            m_state = 'WAITING'

        else:
            # my state depends on launch whose state has the highest 'score'
            # in STATE_RANKS
            m_launch = self._get_representative_launch(fw)
            m_state = m_launch.state if m_launch else 'READY'
            m_action = m_launch.action if (m_launch and m_launch.state == "COMPLETED") else None

            # report any FIZZLED parents if allow_fizzed allows us to handle FIZZLED jobs
            if fw.spec.get('_allow_fizzled_parents'):
                parent_fws = [self.id_fw[p].to_dict() for p in
                              self.links.parent_links.get(fw_id, []) if
                              self.id_fw[p].state == 'FIZZLED']
                if len(parent_fws) > 0:
                    fw.spec['_fizzled_parents'] = parent_fws
                    updated_ids.add(fw_id)

        fw.state = m_state
        # Brings self.fw_states in sync with fw_states in db
        self.fw_states[fw_id] = m_state

        if m_state != prev_state:
            updated_ids.add(fw_id)

            if m_state == 'COMPLETED':
                updated_ids = updated_ids.union(self.apply_action(m_action,
                                                                  fw.fw_id))

            # refresh all the children and other updated ids (note that defuse_workflow option can affect other branches)
            for child_id in updated_ids.union(self.links[fw_id]):
                updated_ids = updated_ids.union(
                    self.refresh(child_id, updated_ids))

        self.updated_on = datetime.utcnow()

        return updated_ids

    @property
    def root_fw_ids(self):
        """
        Gets root FireWorks of this workflow (those with no parents)

        :return: ([int]) Firework ids of root FWs
        """

        all_ids = set(self.links.nodes)
        child_ids = set(self.links.parent_links.keys())
        root_ids = all_ids.difference(child_ids)
        return list(root_ids)

    @property
    def leaf_fw_ids(self):
        """
        Gets leaf FireWorks of this workflow (those with no children)

        :return: ([int]) Firework ids of leaf FWs
        """

        leaf_ids = []
        for id, children in self.links.items():
            if len(children) == 0:
                leaf_ids.append(id)
        return leaf_ids

    def _reassign_ids(self, old_new):
        """
        Internal method to reassign Firework ids, e.g. due to database insertion

        :param old_new: (dict)
        """

        # update id_fw
        new_id_fw = {}
        for (fwid, fws) in self.id_fw.items():
            new_id_fw[old_new.get(fwid, fwid)] = fws
        self.id_fw = new_id_fw

        # update the Links
        new_l = {}
        for (parent, children) in self.links.items():
            new_l[old_new.get(parent, parent)] = [old_new.get(child, child) for
                                                  child in children]
        self.links = Workflow.Links(new_l)

        # update the states
        new_fw_states = {}
        for (fwid, fw_state) in self.fw_states.items():
            new_fw_states[old_new.get(fwid, fwid)] = fw_state
        self.fw_states = new_fw_states

    def to_dict(self):
        return {'fws': [f.to_dict() for f in self.id_fw.values()],
                'links': self.links.to_dict(),
                'name': self.name,
                'metadata': self.metadata, 'updated_on': self.updated_on, 'created_on': self.created_on}

    def to_db_dict(self):
        m_dict = self.links.to_db_dict()
        m_dict['metadata'] = self.metadata
        m_dict['state'] = self.state
        m_dict['name'] = self.name
        m_dict['created_on'] = self.created_on
        m_dict['updated_on'] = self.updated_on
        m_dict['fw_states'] = dict([(str(k), v) for (k, v) in self.fw_states.items()])
        return m_dict

    def to_display_dict(self):
        m_dict = self.to_db_dict()
        nodes = sorted(m_dict['nodes'])
        m_dict['name--id'] = self.name + '--' + str(nodes[0])
        m_dict['launch_dirs'] = OrderedDict(
            [(self._str_fw(x), [l.launch_dir for l in self.id_fw[x].launches])
             for x in nodes])
        m_dict['states'] = OrderedDict(
            [(self._str_fw(x), self.id_fw[x].state) for x in nodes])
        m_dict['nodes'] = [self._str_fw(x) for x in nodes]
        m_dict['links'] = OrderedDict(
            [(self._str_fw(k), [self._str_fw(v) for v in a]) for k, a in
             m_dict['links'].items()])
        m_dict['parent_links'] = OrderedDict(
            [(self._str_fw(k), [self._str_fw(v) for v in a]) for k, a in
             m_dict['parent_links'].items()])
        m_dict['states_list'] = '-'.join([a[0:4] for a in m_dict['states'].values()])
        return m_dict

    def _str_fw(self, fw_id):
        return self.id_fw[int(fw_id)].name + '--' + str(fw_id)

    def _get_representative_launch(self, fw):
        max_score = Firework.STATE_RANKS['ARCHIVED']  # state rank must be greater than this
        m_launch = None

        # TODO: if muliple COMPLETED launches, pick the first launch in terms of end date
        for l in fw.launches:
            if Firework.STATE_RANKS[l.state] > max_score:
                max_score = Firework.STATE_RANKS[l.state]
                m_launch = l

        return m_launch

    @classmethod
    def from_wflow(cls, wflow):
        """Create a fresh Workflow from an existing one.

        """

        new_wf = Workflow.from_dict(wflow.to_dict())
        new_wf.reset(reset_ids=True)

        return new_wf

    def reset(self, reset_ids=True):
        """Reset the states of all Fireworks in this workflow to 'WAITING'.

        :param reset_ids: (bool) if ``True``, give each Firework a new id.

        """
        if reset_ids:
            old_new = {} # mapping between old and new Firework ids
            for fw_id, fw in self.id_fw.items():
                global NEGATIVE_FWID_CTR
                NEGATIVE_FWID_CTR -= 1
                new_id = NEGATIVE_FWID_CTR

                old_new[fw_id] = new_id
                fw.fw_id = new_id
        
            self._reassign_ids(old_new)

        # reset states
        for fw in self.fws:
            fw.state = 'WAITING'

        self.fw_states = {key: self.id_fw[key].state for key in self.id_fw}

    @classmethod
    def from_dict(cls, m_dict):
        # accept either a Workflow dict or a Firework dict
        if 'fws' in m_dict:
            created_on = m_dict.get('created_on')
            updated_on = m_dict.get('updated_on')
            return Workflow([Firework.from_dict(f) for f in m_dict['fws']],
                            Workflow.Links.from_dict(m_dict['links']), m_dict.get('name'),
                            m_dict['metadata'], created_on, updated_on)
        else:
            return Workflow.from_Firework(Firework.from_dict(m_dict))

    @classmethod
    def from_Firework(cls, fw, name=None, metadata=None):
        name = name if name else fw.name
        return Workflow([fw], None, name=name, metadata=metadata, created_on=fw.created_on,
                        updated_on=fw.updated_on)

    def __str__(self):
        return 'Workflow object: (fw_ids: {} , name: {})'.format(self.id_fw.keys(), self.name)
