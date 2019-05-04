# coding: utf-8

from __future__ import unicode_literals

from copy import deepcopy


"""
This module contains:

    - A Firework defines a workflow step and contains one or more Firetasks along with
        a description of its run on a computing resource.
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
from fireworks.utilities.fw_serializers import FWSerializable, recursive_serialize, \
    recursive_deserialize, serialize_fw
from fireworks.utilities.fw_utilities import get_my_host, get_my_ip, NestedClassGetter

from typing import List, Dict, Optional, Union

__author__ = "Anubhav Jain"
__credits__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 5, 2013"


def _new_launch():
    launch = {}
    launch['state'] = None
    launch['state_history'] = {}
    launch['fworker'] = None
    launch['host'] = None
    launch['ip'] = None
    launch['trackers'] = None
    launch['action'] = None
    launch['launch_idx'] = None
    launch['fw_id'] = None
    return launch


##############################################################################
#                           FIRETASK CLASSES                                 #
##############################################################################

@add_metaclass(abc.ABCMeta)
class Firetask(defaultdict, FWSerializable):
    """
    FiretaskBase is used like an abstract class that defines a computing task
    (Firetask). All Firetasks should inherit from FiretaskBase.

    You can set parameters of a Firetask like you'd use a dict.
    """
    # Specify required parameters with class variable. Consistency will be checked upon init.
    required_params = []

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

        for k in self.required_params:
            if k not in self:
                raise ValueError("{}: Required parameter {} not specified!".format(self, k))

    @abc.abstractmethod
    def run_task(self, fw_spec):
        """
        This method gets called when the Firetask is run. It can take in a
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

    # not strictly needed here for pickle/unpickle, but complements __setstate__
    def __getstate__(self):
        return self.to_dict()

    # added to support pickle/unpickle
    def __setstate__(self, state):
        self.__init__(state)

    # added to support pickle/unpickle
    def __reduce__(self):
        t = defaultdict.__reduce__(self)
        return (t[0], (self.to_dict(),), t[2], t[3], t[4])


class BackgroundTask(FWSerializable, object):
    _fw_name = 'BackgroundTask'

    def __init__(self, tasks: List[Firetask], num_launches: int=0,
                 sleep_time: float=60, run_on_finish: bool=False):
        """
        Args:
            tasks [Firetask]: a list of Firetasks to perform
            num_launches (int): the total number of times to run the process (0=infinite)
            sleep_time (int): sleep time in seconds between background runs
            run_on_finish (bool): always run this task upon completion of Firework
        """
        self.tasks = tasks if isinstance(tasks, (list, tuple)) else [tasks]
        self.num_launches = num_launches
        self.sleep_time = sleep_time
        self.run_on_finish = run_on_finish

    @recursive_serialize
    @serialize_fw
    def to_dict(self) -> Dict:
        return {'tasks': self.tasks, 'num_launches': self.num_launches,
                'sleep_time': self.sleep_time, 'run_on_finish': self.run_on_finish}

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict: Dict) -> 'BackgroundTask':
        return BackgroundTask(m_dict['tasks'], m_dict['num_launches'],
                              m_dict['sleep_time'], m_dict['run_on_finish'])

@add_metaclass(abc.ABCMeta)
class FiretaskBase(Firetask):
    pass

@add_metaclass(abc.ABCMeta)
class FireTaskBase(Firetask):
    pass

##############################################################################
#                           FIREWORK CLASS                                   #
##############################################################################

class Firework(FWSerializable):
    """
    A Firework is a workflow step and might be contain several Firetasks.
    It contains the Firetasks to be executed and the state of the execution.
    """

    STATE_RANKS = {'ARCHIVED': -2, 'FIZZLED': -1, 'DEFUSED': 0, 'PAUSED' : 0,
                   'WAITING': 1, 'READY': 2, 'RESERVED': 3, 'RUNNING': 4,
                   'COMPLETED': 5,
                   'OFFLINE-READY': 2, 'OFFLINE-RESERVED': 3, 'OFFLINE-RUNNING': 4}

    def __init__(self, tasks: Union[Firetask, List[Firetask]],
                 spec: Optional[dict]=None, name: Optional[str]=None,
                 state: str='WAITING', created_on: Optional[datetime]=None,
                 fw_id: Optional[int]=None, parents: Union[None, 'Firework', List['Firework']]=None,
                 updated_on: Optional[datetime]=None,
                 fworker: Optional[FWorker]=None,
                 host: Optional[str]=None, ip: Optional[str]=None,
                 trackers: Optional[List['Tracker']]=None,
                 launch_idx: Optional[int]=None,
                 action: Optional['FWAction']=None,
                 launch_dir: Optional[str]=None, 
                 state_history: Optional[dict]=None):

        # launch will contain launch_idx, launch_dir, state, created_on,
        # updated_on, fworker, host, ip, trackers, action, state_history

        # state, created_on, updated_on can be directly queried by Firework

        self.tasks = tasks if isinstance(tasks, (list, tuple)) else [tasks]
        self.spec = spec.copy() if spec else {}
        self.name = name or 'Unnamed FW'
        # names
        if fw_id is not None:
            self.fw_id = fw_id
        else:
            global NEGATIVE_FWID_CTR
            NEGATIVE_FWID_CTR -= 1
            self.fw_id = NEGATIVE_FWID_CTR

        self.launch_idx = launch_idx

        self.launch_dir = launch_dir

        parents = [parents] if isinstance(parents, Firework) else parents
        self.parents = parents if parents else []
        self.created_on = created_on or datetime.utcnow()
        self.updated_on = updated_on or datetime.utcnow()

        launch_info = {'fworker': fworker,
                       'host': host,
                       'ip': ip,
                       'trackers': trackers,
                       'state_history': state_history,
                       'action': action}
        self._setup_launch(launch_info)

        self.state = state

    @recursive_deserialize
    def _setup_launch(self, launch_info):
        self.fworker = launch_info.get('fworker', None) or FWorker()
        self.host = launch_info.get('host', None) or get_my_host()
        self.ip = launch_info.get('ip', None) or get_my_ip()
        self.trackers = launch_info.get('trackers', None) or []

        self.action = launch_info.get('action', None)
        self.state_history = launch_info.get('state_history', None) or []

        if type(self.action) == dict:
            self.action = FWAction.from_dict(self.action)

        self.state = launch_info.get('state', self.state)
        self.launch_dir = launch_info.get('launch_dir', self.launch_dir)
        self.launch_idx = launch_info.get('launch_idx', self.launch_idx)

    def reset_launch(self, state: str='WAITING', launch_dir: str=None,
                     trackers: List['Tracker']=None,
                     state_history: dict=None, fworker: FWorker=None,
                     host: str=None, ip: str=None, launch_idx: int=None):

        launch_info = {'fworker': fworker,
                       'host': host,
                       'ip': ip,
                       'trackers': trackers,
                       'state_history': state_history,
                       'state': state,
                       'launch_dir': launch_dir,
                       'launch_idx': launch_idx}
        self._setup_launch(launch_info)

    # FUNCTIONS FOR ACCESSING AND UPDATING STATE HISTORY

    def touch_history(self, update_time: datetime=None,
                      checkpoint: dict=None):
        """
        Updates the update_on field of the state history of a Launch. Used to ping that a Launch
        is still alive.

        Args:
            update_time (datetime)
        """
        update_time = update_time or datetime.utcnow()
        if checkpoint:
            self.state_history[-1]['checkpoint'] = checkpoint
        self.state_history[-1]['updated_on'] = update_time

    def _update_state_history(self, state: str):
        """
        Internal method to update the state history whenever the Launch state is modified.

        Args:
            state (str)
        """
        now_time = datetime.utcnow()
        self.updated_on = now_time
        if len(self.state_history) > 0:
            last_state = self.state_history[-1]['state']
            last_checkpoint = self.state_history[-1].get('checkpoint', None)
        else:
            last_state, last_checkpoint = None, None
        if state != last_state:
            new_history_entry = {'state': state, 'created_on': now_time}
            if state != "COMPLETED" and last_checkpoint:
                new_history_entry.update({'checkpoint': last_checkpoint})
            self.state_history.append(new_history_entry)
            if state in ['RUNNING', 'RESERVED']:
                self.touch_history()  # add updated_on key

    def _get_time(self, states: List[str], use_update_time: bool=False) -> datetime:
        """
        Internal method to help get the time of various events in the Launch (e.g. RUNNING)
        from the state history.

        Args:
            states (list/tuple): match one of these states
            use_update_time (bool): use the "updated_on" time rather than "created_on"

        Returns:
            (datetime)
        """
        states = states if isinstance(states, (list, tuple)) else [states]
        for data in self.state_history:
            if data['state'] in states:
                if use_update_time:
                    return data['updated_on']
                return data['created_on']

    def set_reservation_id(self, reservation_id: int):
        """
        Adds the job_id to the reservation.

        Args:
            reservation_id (int or str): the id of the reservation (e.g., queue reservation)
        """
        for data in self.state_history:
            if data['state'] == 'RESERVED' and 'reservation_id' not in data:
                data['reservation_id'] = str(reservation_id)
                break

    @property
    def state(self) -> str:
        """
        Returns:
            str: The current state of the Launch.
        """
        if self.state_history and len(self.state_history) > 0:
            return self.state_history[-1]['state']
        else:
            return "WAITING"

    @state.setter
    def state(self, state: str):
        """
        Setter for the the Launch's state. Automatically triggers an update to state_history.

        Args:
            state (str): the state to set for the Launch
        """
        self._update_state_history(state)

    def set_launch_dir(self, launch_dir: str):
        """
        Update the launch_dir. Might change this to a setter later
        """
        self.launch_dir = launch_dir

    @property
    def time_start(self) -> datetime:
        """
        Returns:
            datetime: the time the Launch started RUNNING
        """
        return self._get_time('RUNNING')

    @property
    def time_end(self) -> datetime:
        """
        Returns:
            datetime: the time the Launch was COMPLETED or FIZZLED
        """
        return self._get_time(['COMPLETED', 'FIZZLED'])

    @property
    def time_reserved(self) -> datetime:
        """
        Returns:
            datetime: the time the Launch was RESERVED in the queue
        """
        return self._get_time('RESERVED')

    @property
    def last_pinged(self) -> datetime:
        """
        Returns:
            datetime: the time the Launch last pinged a heartbeat that it was still running
        """
        return self._get_time('RUNNING', True)

    @property
    def runtime_secs(self) -> float:
        """
        Returns:
            float: the number of seconds that the Launch ran for.
        """
        start = self.time_start
        end = self.time_end
        if start and end:
            return (end - start).total_seconds()

    @property
    def reservedtime_secs(self) -> float:
        """
        Returns:
            float: number of seconds the Launch was stuck as RESERVED in a queue.
        """
        start = self.time_reserved
        if start:
            end = self.time_start if self.time_start else datetime.utcnow()
            return (end - start).total_seconds()

    @property
    @recursive_serialize
    def launch(self) -> Dict:
        launch = {}
        launch['state'] = self.state
        launch['state_history'] = self.state_history
        launch['fworker'] = self.fworker
        launch['host'] = self.host
        launch['ip'] = self.ip
        launch['trackers'] = self.trackers
        launch['action'] = self.action
        launch['launch_idx'] = self.launch_idx
        launch['launch_dir'] = self.launch_dir
        launch['fw_id'] = self.fw_id
        return launch

    @recursive_serialize
    def to_dict(self) -> Dict:
        # put tasks in a special location of the spec
        spec = self.spec
        spec['_tasks'] = [t.to_dict() for t in self.tasks]
        m_dict = {'spec': spec, 'fw_id': self.fw_id, 'created_on': self.created_on,
                  'updated_on': self.updated_on}

        # keep export of new FWs to files clean
        #if self.state != 'WAITING':
        #    m_dict['state'] = self.state
        m_dict['state'] = self.state

        m_dict['name'] = self.name

        m_dict['launch'] = self.launch

        return m_dict

    @recursive_serialize
    def to_db_dict(self) -> Dict:
        m_d = self.to_dict()
        m_d['launch']['time_start'] = self.time_start
        m_d['launch']['time_end'] = self.time_end
        m_d['launch']['runtime_secs'] = self.runtime_secs
        if self.reservedtime_secs:
            m_d['launch']['reservedtime_secs'] = self.reservedtime_secs
        return m_d

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict: dict) -> 'Firework':
        tasks = m_dict['spec']['_tasks']
        fw_id = m_dict.get('fw_id', -1)
        name = m_dict.get('name', None)
        state = m_dict.get('state', 'WAITING')

        launch = m_dict.get('launch', {})
        created_on = m_dict.get('created_on')
        updated_on = m_dict.get('updated_on')
        launch_idx = launch.get('launch_idx', None)
        fworker = FWorker.from_dict(launch['fworker']) if launch.get('fworker', None) else None
        action = FWAction.from_dict(launch['action']) if launch.get('action', None) else None
        trackers = [Tracker.from_dict(f) for f in launch['trackers']]\
                    if launch.get('trackers', None) else None
        launch_dir = launch.get('launch_dir', None)
        host = launch.get('host', None)
        ip = launch.get('ip', None)
        state_history = launch.get('state_history', None)

        return Firework(tasks=tasks, spec=m_dict['spec'], name=name, state=state,
                        created_on=created_on, fw_id=fw_id, updated_on=updated_on,
                        fworker=fworker, host=host, ip=ip, trackers=trackers,
                        launch_idx=launch_idx, action=action,
                        launch_dir=launch_dir, state_history=state_history)

    def _rerun(self):
        """
        Moves all Launches to archived Launches and resets the state to 'WAITING'. The Firework
        can thus be re-run even if it was Launched in the past. This method should be called by
        a Workflow because a refresh is needed after calling this method.
        """
        if self.state == 'FIZZLED':
            last_launch = self.launch
            if (EXCEPT_DETAILS_ON_RERUN and self.action and
                self.action.stored_data.get('_exception', {}).get('_details')):
                # add the exception details to the spec
                self.spec['_exception_details'] = self.action.stored_data['_exception']['_details']
            else:
                # clean spec from stale details
                self.spec.pop('_exception_details', None)

        #self.archived_launches.extend(self.launches)
        #self.archived_launches = list(set(self.archived_launches))  # filter duplicates
        self.reset_launch(launch_idx=None)

    def copy(self) -> 'Firework':
        return Firework.from_dict(self.to_dict())

    def __str__(self):
        return 'Firework object: (id: %i , name: %s)' % (self.fw_id, self.fw_name)


class Tracker(FWSerializable, object):
    """
    A Tracker monitors a file and returns the last N lines for updating the Launch object.
    """

    MAX_TRACKER_LINES = 1000

    def __init__(self, filename: str, nlines: int=TRACKER_LINES,
                 content: str='', allow_zipped: bool=False):
        """
        Args:
            filename (str)
            nlines (int): number of lines to track
            content (str): tracked content
            allow_zipped (bool): if set, will look for zipped file.
        """
        if nlines > self.MAX_TRACKER_LINES:
            raise ValueError("Tracker only supports a maximum of {} lines; you put {}.".format(
                self.MAX_TRACKER_LINES, nlines))
        self.filename = filename
        self.nlines = nlines
        self.content = content
        self.allow_zipped = allow_zipped

    def track_file(self, launch_dir: str=None) -> str:
        """
        Reads the monitored file and returns back the last N lines

        Args:
            launch_dir (str): directory where job was launched in case of relative filename

        Returns:
            str: the content(last N lines)
        """
        m_file = self.filename
        if launch_dir and not os.path.isabs(self.filename):
            m_file = os.path.join(launch_dir, m_file)
        lines = []
        if self.allow_zipped:
            m_file = zpath(m_file)
        if os.path.exists(m_file):
            with zopen(m_file, "rt") as f:
                for l in reverse_readline(f):
                    lines.append(l)
                    if len(lines) == self.nlines:
                        break
            self.content = '\n'.join(reversed(lines))
        return self.content

    def to_dict(self) -> dict:
        m_dict = {'filename': self.filename, 'nlines': self.nlines, 'allow_zipped': self.allow_zipped}
        if self.content:
            m_dict['content'] = self.content
        return m_dict

    @classmethod
    def from_dict(cls, m_dict: dict):
        return Tracker(m_dict['filename'], m_dict['nlines'], m_dict.get('content', ''),
                       m_dict.get('allow_zipped', False))

    def __str__(self):
        return '### Filename: {}\n{}'.format(self.filename, self.content)

##############################################################################
#                           WORKFLOW CLASS                                   #
##############################################################################

class Workflow(FWSerializable):
    """
    A Workflow connects a group of FireWorks in an execution order.
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
        def nodes(self) -> List[int]:
            """ Return list of all nodes"""
            allnodes = list(self.keys())
            for v in self.values():
                allnodes.extend(v)
            return list(set(allnodes))

        @property
        def parent_links(self) -> Dict:
            """
            Return a dict of child and its parents.

            Note: if performance of parent_links becomes an issue, override delitem/setitem to
            update parent_links
            """
            child_parents = defaultdict(list)
            for (parent, children) in self.items():
                for child in children:
                    child_parents[child].append(parent)
            return dict(child_parents)

        def to_dict(self) -> Dict:
            """
            Convert to str form for Mongo, which cannot have int keys.

            Returns:
                dict
            """
            return dict([(str(k), v) for (k, v) in self.items()])

        def to_db_dict(self) -> Dict:
            """
            Convert to str form for Mongo, which cannot have int keys .

            Returns:
                dict
            """
            m_dict = {
                'links': dict([(str(k), v) for (k, v) in self.items()]),
                'parent_links': dict([(str(k), v) for (k, v) in self.parent_links.items()]),
                'nodes': self.nodes}
            return m_dict

        @classmethod
        def from_dict(cls, m_dict) -> 'Workflow.Links':
            return Workflow.Links(m_dict)

        def __setstate__(self, state: str):
            for k, v in state:
                self[k] = v

        def __reduce__(self):
            """
            To support Pickling of inner classes (for multi-job launcher's multiprocessing).
            Return a class which can return this class when called with the appropriate tuple of
            arguments
            """
            state = list(self.items())
            return NestedClassGetter(), (Workflow, self.__class__.__name__, ), state

    def __init__(self, fireworks: List[Firework], links_dict: Dict=None,
                 name: str=None, metadata: Dict=None,
                 created_on: datetime=None, updated_on: datetime=None,
                 fw_states: Dict=None):
        """
        Args:
            fireworks ([Firework]): all FireWorks in this workflow.
            links_dict (dict): links between the FWs as (parent_id):[(child_id1, child_id2)]
            name (str): name of workflow.
            metadata (dict): metadata for this Workflow.
            created_on (datetime): time of creation
            updated_on (datetime): time of update
            fw_states (dict): leave this alone unless you are purposefully creating a Lazy-style WF
        """
        name = name or 'unnamed WF'  # prevent None names

        links_dict = links_dict if links_dict else {}

        # main dict containing mapping of an id to a Firework object
        self.id_fw = {}
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
                        "FW_id: {} defines a dependent link to FW_id: {}, but the latter was not "
                        "added to the workflow!".format(fw.fw_id, pfw.fw_id))
                if fw.fw_id not in self.links[pfw.fw_id]:
                    self.links[pfw.fw_id].append(fw.fw_id)

        self.name = name

        # sanity check: make sure the set of nodes from the links_dict is equal to the set
        # of nodes from id_fw
        if set(self.links.nodes) != set(map(int, self.id_fw.keys())):
            raise ValueError("Specified links don't match given FW")

        if len(self.links.nodes) == 0:
            raise ValueError("Workflow cannot be empty (must contain at least 1 FW)")

        self.metadata = metadata if metadata else {}
        self.created_on = created_on or datetime.utcnow()
        self.updated_on = updated_on or datetime.utcnow()

        # dict containing mapping of an id to a firework state. The states are stored locally and
        # redundantly for speed purpose
        if fw_states:
            self.fw_states = fw_states
        else:
            self.fw_states = {key:self.id_fw[key].state for key in self.id_fw}

    @property
    def fws(self) -> List[Firework]:
        """
        Return list of all fireworks
        """
        return list(self.id_fw.values())

    @property
    def state(self) -> str:
        """
        Returns:
            state (str): state of workflow
        """
        m_state = 'READY'
        #states = [fw.state for fw in self.fws]
        states = self.fw_states.values()
        leaf_fw_ids = self.leaf_fw_ids  # to save recalculating this

        leaf_states = (self.fw_states[fw_id] for fw_id in leaf_fw_ids)
        if all(s == 'COMPLETED' for s in leaf_states):
            m_state = 'COMPLETED'
        elif all(s == 'ARCHIVED' for s in states):
            m_state = 'ARCHIVED'
        elif any(s == 'DEFUSED' for s in states):
            m_state = 'DEFUSED'
        elif any(s == 'PAUSED' for s in states):
            m_state = 'PAUSED'
        elif any(s == 'FIZZLED' for s in states):
            fizzled_ids = (fw_id for fw_id, state in self.fw_states.items()
                           if state == 'FIZZLED')
            for fizzled_id in fizzled_ids:
                # If a fizzled fw is a leaf fw, then the workflow is fizzled
                if (fizzled_id in leaf_fw_ids or
                    # Otherwise all children must be ok with the fizzled parent
                    not all(self.id_fw[child_id].spec.get('_allow_fizzled_parents', False)
                            for child_id in self.links[fizzled_id])):
                    m_state = 'FIZZLED'
                    break
            else:
                m_state = 'RUNNING'
        elif any(s == 'COMPLETED' for s in states) or any(s == 'RUNNING' for s in states):
            m_state = 'RUNNING'
        elif any(s == 'RESERVED' for s in states):
            m_state = 'RESERVED'
        return m_state

    def apply_action(self, action: 'FWAction', fw_id: int) -> List[int]:
        """
        Apply a FWAction on a Firework in the Workflow.

        Args:
            action (FWAction): action to apply
            fw_id (int): id of Firework on which to apply the action

        Returns:
            [int]: list of Firework ids that were updated or new
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
                self.fw_states[cfid] = 'DEFUSED'
                updated_ids.append(cfid)

        # defuse workflow
        if action.defuse_workflow:
            for fw_id in self.links.nodes:
                if self.id_fw[fw_id].state not in ['FIZZLED', 'COMPLETED']:
                    self.id_fw[fw_id].state = 'DEFUSED'
                    self.fw_states[fw_id] = 'DEFUSED'
                    updated_ids.append(fw_id)

        # add detour FireWorks. This should be done *before* additions
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

    def rerun_fw(self, fw_id: int, updated_ids: List[int]=None) -> List[int]:
        """
        Archives the launches of a Firework so that it can be re-run.

        Args:
            fw_id (int): id of firework to be rerun
            updated_ids (set(int)): set of fireworks id to rerun

        Returns:
            [int]: list of Firework ids that were updated
        """

        updated_ids = updated_ids if updated_ids else set()
        m_fw = self.id_fw[fw_id]
        m_fw._rerun()
        updated_ids.add(fw_id)

        # refresh the states of the current fw before rerunning the children
        # so that they get the correct state of the parent.
        updated_ids.union(self.refresh(fw_id, updated_ids))

        # re-run all the children
        for child_id in self.links[fw_id]:
            if self.id_fw[child_id].state != 'WAITING':
                updated_ids = updated_ids.union(self.rerun_fw(child_id, updated_ids))

        return updated_ids

    def append_wf(self, new_wf: 'Workflow', fw_ids: List[int], detour: bool=False,
                  pull_spec_mods: bool=False) -> List[int]:
        """
        Method to add a workflow as a child to a Firework
        Note: detours must have children that have STATE_RANK that is WAITING or below

        Args:
            new_wf (Workflow): New Workflow to add.
            fw_ids ([int]): ids of the parent Fireworks on which to add the Workflow.
            detour (bool): add children of the current Firework to the Workflow's leaves.
            pull_spec_mods (bool): pull spec mods of COMPLETED parents, refreshes the WF states.

        Returns:
            [int]: list of Firework ids that were updated or new
        """
        updated_ids = []

        root_ids = new_wf.root_fw_ids
        leaf_ids = new_wf.leaf_fw_ids

        # make sure detour runs do not link to ready/running/completed/etc. runs
        if detour:
            for fw_id in fw_ids:
                if fw_id in self.links:
                    # make sure all of these links are WAITING, else the DETOUR is not well defined
                    ready_run = [(f >= 0 and Firework.STATE_RANKS[self.fw_states[f]] > 1)
                                 for f in self.links[fw_id]]
                    if any(ready_run):
                        raise ValueError("fw_id: {}: Detour option only works if all children "
                                         "of detours are not READY to run and have not "
                                         "already run".format(fw_id))

        # make sure all new child fws have negative fw_id
        for new_fw in new_wf.fws:
            if new_fw.fw_id >= 0:  # note: this is also used later in the 'detour' code
                raise ValueError(
                    'FireWorks to add must use a negative fw_id! Got fw_id: {}'.format(new_fw.fw_id))

        # completed checks - go ahead and append
        for new_fw in new_wf.fws:
            self.id_fw[new_fw.fw_id] = new_fw  # add new_fw to id_fw

            if new_fw.fw_id in leaf_ids:
                if detour:
                    for fw_id in fw_ids:
                        # add children of current FW to new FW
                        self.links[new_fw.fw_id] = [f for f in self.links[fw_id] if f >= 0]
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
                    #m_launch = self._get_representative_launch(m_fw)  # get Launch of parent
                    if m_fw:
                        # pull spec update
                        if m_fw.state == 'COMPLETED' and m_fw.action.update_spec:
                            new_wf.id_fw[root_id].spec.update(m_fw.action.update_spec)
                        # pull spec mods
                        if m_fw.state == 'COMPLETED' and m_fw.action.mod_spec:
                            for mod in m_fw.action.mod_spec:
                                apply_mod(mod, new_wf.id_fw[root_id].spec)

        for new_fw in new_wf.fws:
            updated_ids = self.refresh(new_fw.fw_id, set(updated_ids))

        return updated_ids

    def refresh(self, fw_id: int, updated_ids: List[int]=None) -> List[int]:
        """
        Refreshes the state of a Firework and any affected children.

        Args:
            fw_id (int): id of the Firework on which to perform the refresh
            updated_ids ([int])

        Returns:
            set(int): list of Firework ids that were updated
        """
        # these are the fw_ids to re-enter into the database
        updated_ids = updated_ids if updated_ids else set()

        fw = self.id_fw[fw_id]
        prev_state = fw.state

        # if we're paused, defused or archived, just skip altogether
        if fw.state == 'DEFUSED' or fw.state == 'ARCHIVED' or fw.state == 'PAUSED':
            self.fw_states[fw_id] = fw.state
            return updated_ids

        completed_parent_states = ['COMPLETED']
        if fw.spec.get('_allow_fizzled_parents'):
            completed_parent_states.append('FIZZLED')

        # check parent states for any that are not completed
        for parent in self.links.parent_links.get(fw_id, []):
            if self.fw_states[parent] not in completed_parent_states:
                m_state = 'WAITING'
                break

        else:  # not DEFUSED/ARCHIVED, and all parents are done running. Now the state depends on the launch status
            # my state depends on launch whose state has the highest 'score' in STATE_RANKS
            m_state = fw.state if fw.state != 'WAITING' else 'READY'
            m_action = fw.action if (m_state == "COMPLETED") else None

            # report any FIZZLED parents if allow_fizzed allows us to handle FIZZLED jobs
            if fw.spec.get('_allow_fizzled_parents') and "_fizzled_parents" not in fw.spec:
                parent_fws = [self.id_fw[p].to_dict() for p in self.links.parent_links.get(fw_id, [])
                              if self.id_fw[p].state == 'FIZZLED']
                if len(parent_fws) > 0:
                    fw.spec['_fizzled_parents'] = parent_fws
                    updated_ids.add(fw_id)

        fw.state = m_state
        # Brings self.fw_states in sync with fw_states in db
        self.fw_states[fw_id] = m_state

        #if m_state != prev_state:
        if True:
            updated_ids.add(fw_id)

            if m_state == 'COMPLETED':
                updated_ids = updated_ids.union(self.apply_action(m_action, fw.fw_id))

            # refresh all the children that could possibly now be READY to run
            # note that "FIZZLED" is for _allow_fizzled_parents children
            if m_state in ['COMPLETED', 'FIZZLED']:
                for child_id in self.links[fw_id]:
                    updated_ids = updated_ids.union(self.refresh(child_id, updated_ids))

        self.updated_on = datetime.utcnow()

        return updated_ids

    @property
    def root_fw_ids(self) -> List[int]:
        """
        Gets root FireWorks of this workflow (those with no parents).

        Returns:
            [int]: Firework ids of root FWs
        """
        all_ids = set(self.links.nodes)
        child_ids = set(self.links.parent_links.keys())
        root_ids = all_ids.difference(child_ids)
        return list(root_ids)

    @property
    def leaf_fw_ids(self) -> List[int]:
        """
        Gets leaf FireWorks of this workflow (those with no children).

        Returns:
            [int]: Firework ids of leaf FWs
        """
        leaf_ids = []
        for id, children in self.links.items():
            if len(children) == 0:
                leaf_ids.append(id)
        return leaf_ids

    def _reassign_ids(self, old_new: Dict):
        """
        Internal method to reassign Firework ids, e.g. due to database insertion.

        Args:
            old_new (dict)
        """
        # update id_fw
        new_id_fw = {}
        for (fwid, fws) in self.id_fw.items():
            new_id_fw[old_new.get(fwid, fwid)] = fws
        self.id_fw = new_id_fw

        # update the Links
        new_l = {}
        for (parent, children) in self.links.items():
            new_l[old_new.get(parent, parent)] = [old_new.get(child, child) for child in children]
        self.links = Workflow.Links(new_l)

        # update the states
        new_fw_states = {}
        for (fwid, fw_state) in self.fw_states.items():
            new_fw_states[old_new.get(fwid, fwid)] = fw_state
        self.fw_states = new_fw_states

    def to_dict(self) -> Dict:
        return {'fws': [f.to_dict() for f in self.id_fw.values()],
                'links': self.links.to_dict(),
                'name': self.name,
                'metadata': self.metadata,
                'updated_on': self.updated_on,
                'created_on': self.created_on}

    def to_db_dict(self) -> Dict:
        m_dict = self.links.to_db_dict()
        m_dict['metadata'] = self.metadata
        m_dict['state'] = self.state
        m_dict['name'] = self.name
        m_dict['created_on'] = self.created_on
        m_dict['updated_on'] = self.updated_on
        m_dict['fw_states'] = dict([(str(k), v) for (k, v) in self.fw_states.items()])
        return m_dict

    def to_display_dict(self) -> Dict:
        m_dict = self.to_db_dict()
        nodes = sorted(m_dict['nodes'])
        m_dict['name--id'] = self.name + '--' + str(nodes[0])
        m_dict['launch_dirs'] = OrderedDict([(self._str_fw(x), [self.id_fw[x].launch_dir])
                                             for x in nodes])
        m_dict['states'] = OrderedDict([(self._str_fw(x), self.id_fw[x].state) for x in nodes])
        m_dict['nodes'] = [self._str_fw(x) for x in nodes]
        m_dict['links'] = OrderedDict([(self._str_fw(k), [self._str_fw(v) for v in a])
                                       for k, a in m_dict['links'].items()])
        m_dict['parent_links'] = OrderedDict([(self._str_fw(k), [self._str_fw(v) for v in a])
                                              for k, a in m_dict['parent_links'].items()])
        m_dict['states_list'] = '-'.join([a[0:4] for a in m_dict['states'].values()])
        return m_dict

    def _str_fw(self, fw_id: int) -> str:
        """
        Get a string representation of the firework with the given id.

        Args:
            fw_id (int): firework id

        Returns:
            str
        """
        return self.id_fw[int(fw_id)].name + '--' + str(fw_id)

    @classmethod
    def from_wflow(cls, wflow: 'Workflow') -> 'Workflow':
        """
        Create a fresh Workflow from an existing one.

        Args:
            wflow (Workflow)

        Returns:
            Workflow
        """
        new_wf = Workflow.from_dict(wflow.to_dict())
        new_wf.reset(reset_ids=True)
        return new_wf

    def reset(self, reset_ids: bool=True):
        """
        Reset the states of all Fireworks in this workflow to 'WAITING'.

        Args:
            reset_ids (bool): if ``True``, give each Firework a new id.
        """
        if reset_ids:
            old_new = {}  # mapping between old and new Firework ids
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
    def from_dict(cls, m_dict: Dict) -> 'Workflow':
        """
        Return Workflow from its dict representation.

        Args:
            m_dict (dict): either a Workflow dict or a Firework dict

        Returns:
            Workflow
        """
        # accept
        if 'fws' in m_dict:
            created_on = m_dict.get('created_on')
            updated_on = m_dict.get('updated_on')
            return Workflow([Firework.from_dict(f) for f in m_dict['fws']],
                            Workflow.Links.from_dict(m_dict['links']), m_dict.get('name'),
                            m_dict['metadata'], created_on, updated_on)
        else:
            return Workflow.from_Firework(Firework.from_dict(m_dict))

    @classmethod
    def from_Firework(cls, fw: Firework, name: str=None,
                      metadata: Dict=None) -> Firework:
        """
        Return Workflow from the given Firework.

        Args:
            fw (Firework)
            name (str): New workflow's name. if not provided, the firework name is used
            metadata (dict): New workflow's metadata.

        Returns:
            Workflow
        """
        name = name if name else fw.name
        return Workflow([fw], None, name=name, metadata=metadata, created_on=fw.created_on,
                        updated_on=fw.updated_on)

    def __str__(self):
        return 'Workflow object: (fw_ids: {} , name: {})'.format(self.id_fw.keys(), self.name)

    def remove_fws(self, fw_ids: List[int]):
        """
        Remove the fireworks corresponding to the input firework ids and update the workflow i.e the
        parents of the removed fireworks become the parents of the children fireworks (only if the
        children dont have any other parents).

        Args:
            fw_ids (list): list of fw ids to remove.

        """
        # not working with the copies, causes spurious behavior
        wf_dict = deepcopy(self.as_dict())
        orig_parent_links = deepcopy(self.links.parent_links)
        fws = wf_dict["fws"]

        # update the links dict: remove fw_ids and link their parents to their children (if they don't
        # have any other parents).
        for fid in fw_ids:
            children = wf_dict["links"].pop(str(fid))
            # root node --> no parents
            try:
                parents = orig_parent_links[int(fid)]
            except KeyError:
                parents = []
            # remove the firework from their parent links and re-link their parents to the children.
            for p in parents:
                wf_dict["links"][str(p)].remove(fid)
                # adopt the children
                for c in children:
                    # adopt only if the child doesn't have any other parents.
                    if len(orig_parent_links[int(c)]) == 1:
                        wf_dict["links"][str(p)].append(c)

        # update the list of fireworks.
        wf_dict["fws"] = [f for f in fws if f["fw_id"] not in fw_ids]

        new_wf = Workflow.from_dict(wf_dict)
        self.fw_states = new_wf.fw_states
        self.id_fw = new_wf.id_fw
        self.links = new_wf.links


class FWAction(FWSerializable):
    """
    A FWAction encapsulates the output of a Firetask (it is returned by a Firetask after the
    Firetask completes). The FWAction allows a user to store rudimentary output data as well
    as return commands that alter the workflow.
    """

    def __init__(self, stored_data: dict=None, exit: bool=False,
                 update_spec: dict=None, mod_spec: List[dict]=None,
                 additions: List['Workflow']=None, detours: List['Workflow']=None,
                 defuse_children: bool=False, defuse_workflow: bool=False):
        """
        Args:
            stored_data (dict): data to store from the run. Does not affect the operation of FireWorks.
            exit (bool): if set to True, any remaining Firetasks within the same Firework are skipped.
            update_spec (dict): specifies how to update the child FW's spec
            mod_spec ([dict]): update the child FW's spec using the DictMod language (more flexible
                than update_spec)
            additions ([Workflow]): a list of WFs/FWs to add as children
            detours ([Workflow]): a list of WFs/FWs to add as children (they will inherit the
                current FW's children)
            defuse_children (bool): defuse all the original children of this Firework
            defuse_workflow (bool): defuse all incomplete steps of this workflow
        """
        mod_spec = mod_spec if mod_spec is not None else []
        additions = additions if additions is not None else []
        detours = detours if detours is not None else []

        self.stored_data = stored_data if stored_data else {}
        self.exit = exit
        self.update_spec = update_spec if update_spec else {}
        self.mod_spec = mod_spec if isinstance(mod_spec, (list, tuple)) else [mod_spec]
        self.additions = additions if isinstance(additions, (list, tuple)) else [additions]
        self.detours = detours if isinstance(detours, (list, tuple)) else [detours]
        self.defuse_children = defuse_children
        self.defuse_workflow = defuse_workflow

    @recursive_serialize
    def to_dict(self) -> dict:
        return {'stored_data': self.stored_data,
                'exit': self.exit,
                'update_spec': self.update_spec,
                'mod_spec': self.mod_spec,
                'additions': self.additions,
                'detours': self.detours,
                'defuse_children': self.defuse_children,
                'defuse_workflow': self.defuse_workflow}

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict: dict) -> 'FWAction':
        d = m_dict
        additions = [Workflow.from_dict(f) for f in d['additions']]
        detours = [Workflow.from_dict(f) for f in d['detours']]
        return FWAction(d['stored_data'], d['exit'], d['update_spec'],
                        d['mod_spec'], additions, detours,
                        d['defuse_children'], d.get('defuse_workflow', False))

    @property
    def skip_remaining_tasks(self) -> bool:
        """
        If the FWAction gives any dynamic action, we skip the subsequent Firetasks

        Returns:
            bool
        """
        return self.exit or self.detours or self.additions or self.defuse_children or self.defuse_workflow

    def __str__(self):
        return "FWAction\n" + pprint.pformat(self.to_dict())