#!/usr/bin/env python

"""
This module contains some of the most central FireWorks classes:

- A FireTaskBase defines the contract for tasks that run within a FireWork (FireTasks)
- A FWAction encapsulates the output of a FireTask and tells FireWorks what to do next after a job completes
- A FireWork defines a workflow step and contains one or more FireTasks.
- A Launch describes the run of a FireWork on a computing resource.
"""

import datetime
from fireworks.core.fworker import FWorker
from fireworks.utilities.fw_serializers import FWSerializable, recursive_serialize, recursive_deserialize, serialize_fw
from fireworks.utilities.fw_utilities import get_my_host, get_my_ip

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 5, 2013"


class FireTaskBase(FWSerializable):
    """
    FireTaskBase is used as an abstract class that defines a computing task (FireTask). All FireTasks
    should inherit from FireTaskBase.
    """

    def __init__(self, parameters=None):
        """
        :param parameters: (dict) Parameters that control the FireTask's operation (custom depending on the FireTask
        type)
        """

        # When implementing a FireTask, add the following line to the init() to get to_dict to work automatically
        self.parameters = parameters if parameters else {}

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
        return {"parameters": self.parameters}

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        return cls(m_dict['parameters'])


class FWAction(FWSerializable):
    """
    A FWAction encapsulates the output of a FireTask (it is returned by a FireTask after the FireTask completes). The
     FWAction allows a user to store rudimentary output data as well as return commands that alter the workflow.
    """

    commands = ['CONTINUE', 'DEFUSE', 'MODIFY', 'DETOUR', 'CREATE', 'PHOENIX', 'BREAK']

    def __init__(self, command, stored_data=None, mod_spec=None):
        """
        :param command: (str) an item from the list of FWAction.commands
        :param stored_data: (dict) any output data to store. Intended to be brief, not store a ton of data.
        :param mod_spec: description of how to modify the Workflow according to a set of rules (see tutorial docs)
        """
        if command not in FWAction.commands:
            raise ValueError("Invalid command: " + command)

        self.command = command
        self.stored_data = stored_data if stored_data else {}
        self.mod_spec = mod_spec if mod_spec else {}

    @recursive_serialize
    def to_dict(self):
        return {"action": self.command, "stored_data": self.stored_data, "mod_spec": self.mod_spec}

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        if 'create_fw' in m_dict['mod_spec']:
            m_dict['mod_spec']['create_fw'] = FireWork.from_dict(m_dict['mod_spec']['create_fw'])
        return FWAction(m_dict['action'], m_dict['stored_data'], m_dict['mod_spec'])


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

    def to_db_dict(self):
        m_d = self.to_dict()
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