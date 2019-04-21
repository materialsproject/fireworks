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

from fireworks.core.firetask import Firetask, FWAction
from fireworks import Workflow
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

class Firework(FWSerializable):
    """
    A Firework is a workflow step and might be contain several Firetasks.
    It contains the Firetasks to be executed and the state of the execution.
    """

    STATE_RANKS = {'ARCHIVED': -2, 'FIZZLED': -1, 'DEFUSED': 0, 'PAUSED' : 0,
                   'WAITING': 1, 'READY': 2, 'RESERVED': 3, 'RUNNING': 4,
                   'COMPLETED': 5}

    def __init__(self, tasks: Union[Firetask, List[Firetask]], launch_dir: str=None,
                 spec: dict=None, name: str=None, state: str='WAITING',
                 fworker: FWorker=None, host: str=None, ip: str=None,
                 trackers: List['Tracker']=None, fw_id: Optional[int]=None,
                 launch_idx: int=None, parents: List['Firework']=None,
                 created_on: datetime=None,
                 updated_on: datetime=None,
                 action: FWAction=None, state_history: dict=None):

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

    def reset_launch(self, state: str, launch_dir: str, trackers: List['Tracker'],
                     state_history: dict, fworker: FWorker, host: str,
                     ip: str, launch_idx: int):

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
    def state(self):
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
    def time_start(self):
        """
        Returns:
            datetime: the time the Launch started RUNNING
        """
        return self._get_time('RUNNING')

    @property
    def time_end(self):
        """
        Returns:
            datetime: the time the Launch was COMPLETED or FIZZLED
        """
        return self._get_time(['COMPLETED', 'FIZZLED'])

    @property
    def time_reserved(self):
        """
        Returns:
            datetime: the time the Launch was RESERVED in the queue
        """
        return self._get_time('RESERVED')

    @property
    def last_pinged(self):
        """
        Returns:
            datetime: the time the Launch last pinged a heartbeat that it was still running
        """
        return self._get_time('RUNNING', True)

    @property
    def runtime_secs(self):
        """
        Returns:
            int: the number of seconds that the Launch ran for.
        """
        start = self.time_start
        end = self.time_end
        if start and end:
            return (end - start).total_seconds()

    @property
    def reservedtime_secs(self):
        """
        Returns:
            int: number of seconds the Launch was stuck as RESERVED in a queue.
        """
        start = self.time_reserved
        if start:
            end = self.time_start if self.time_start else datetime.utcnow()
            return (end - start).total_seconds()

    @property
    @recursive_serialize
    def launch(self):
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
    def to_dict(self):
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
    def to_db_dict(self):
        m_d = self.to_dict()
        m_d['launch']['time_start'] = self.time_start
        m_d['launch']['time_end'] = self.time_end
        m_d['launch']['runtime_secs'] = self.runtime_secs
        if self.reservedtime_secs:
            m_d['launch']['reservedtime_secs'] = self.reservedtime_secs
        return m_d

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict: dict):
        tasks = m_dict['spec']['_tasks']
        fw_id = m_dict.get('fw_id', -1)
        name = m_dict.get('name', None)
        state = m_dict['state']

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

        return Firework(tasks, launch_dir, m_dict['spec'], name, state,
                        fworker, host, ip, trackers, fw_id, launch_idx,
                        #m_dict['parents'], created_on=created_on, updated_on=updated_on,
                        created_on=created_on, updated_on=updated_on,
                        action=action, state_history=state_history)

    def copy(self):
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
