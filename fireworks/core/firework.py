#!/usr/bin/env python

"""
A FireWork defines a workflow step.

An FWorkflow connects FireWorks by their fw_ids.

A Launch is a describes a FireWork's run on a computing resource. The same Launch might apply to multiple FireWorks,
e.g. if they are identical.

A FWAction encapsulates the output of that launch.
"""

import datetime
from fireworks.core.fw_constants import LAUNCH_RANKS
from fireworks.core.fworker import FWorker
from fireworks.utilities.fw_serializers import FWSerializable, recursive_serialize, recursive_deserialize, serialize_fw

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 5, 2013"


# TODO: add ability to block ports

class FireWork(FWSerializable):
    def __init__(self, tasks, spec=None, fw_id=-1, launches=None, state='WAITING', created_at=None):
        """
        TODO: add more docs
        
        reserved spec keywords:
            _tasks - a list of FireTasks to run
            _priority - the priority of the FW
            _dupefinder - a DupeFinder object, for avoiding duplicates
        
        :param tasks: a list of FireTasks
        :param spec: a dict specification of the job to run
        :param fw_id: the FW's database id to the LaunchPad. Negative numbers will be re-assigned dynamically when
        they are entered in the database through the LaunchPad.
        :param launches: a list of Launch objects of this FireWork
        :param state: the state of the FW (e.g. WAITING, RUNNING, COMPLETED, CANCELED)
        """
        # transform tasks into a list, if not in that format
        if not isinstance(tasks, list):
            tasks = [tasks]

        self.tasks = tasks
        self.spec = spec if spec else {}
        self.spec['_tasks'] = [t.to_dict() for t in tasks]
        self.fw_id = fw_id
        self.launches = launches if launches else []
        self.created_at = created_at if created_at else datetime.datetime.utcnow()
        self.state = state

    @recursive_serialize
    def to_dict(self):
        """
        This is a 'minimal' or 'compact' dict representation of the FireWork
        """
        m_dict = {'spec': self.spec, 'fw_id': self.fw_id, 'created_at': self.created_at}

        if len(self.launches) > 0:
            m_dict['launches'] = self.launches

        if self.state != 'WAITING':
            m_dict['state'] = self.state

        return m_dict

    def to_db_dict(self):
        """
        """
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
        created_at = m_dict.get('created_at', None)

        return FireWork(tasks, m_dict['spec'], fw_id, l, state, created_at)


class FireTaskBase(FWSerializable):
    """
    TODO: add docs
    """

    def __init__(self, parameters=None):
        # Add the following line to your FireTasks to get to_dict to work
        self.parameters = parameters if parameters else {}

    def run_task(self, fw):
        raise NotImplementedError('Need to implement run_task!')

    @serialize_fw
    @recursive_serialize
    def to_dict(self):
        return {"parameters": self.parameters}

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        return cls(m_dict['parameters'])

        # TODO: Task for committing a file to DB?
        # TODO: add checkpoint function


class FWAction():
    """
    TODO: add docs

    """
    # TODO: DETOUR can be merged into ADD (probably)

    commands = ['CONTINUE', 'DEFUSE', 'MODIFY', 'DETOUR', 'CREATE', 'PHOENIX', 'BREAK']

    def __init__(self, command, stored_data=None, mod_spec=None):
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


class Launch(FWSerializable):
    # TODO: add an expiration date
    def __init__(self, fworker, fw_id, host=None, ip=None, launch_dir=None, action=None, start=None, end=None,
                 state=None,
                 launch_id=None):
        """

        :param fworker: A FWorker object describing the worker
        :param fw_id: id of the FireWork this launch is running
        :param host: the hostname where the launch took place (probably automatically set)
        :param ip: the ip address where the launch took place (probably automatically set)
        :param launch_dir: the directory on the host where the launch took place (probably automatically set)
        :param action: The resulting Action from the launch (set after the launch finished)
        :param state: the state of the Launch
        :param launch_id: the id of the Launch for the LaunchPad
        """
        if state not in LAUNCH_RANKS:
            raise ValueError("Invalid launch state: {}".format(state))

        self.fworker = fworker
        self.fw_id = fw_id
        self.host = host
        self.ip = ip
        self.launch_dir = launch_dir
        self.action = action if action else None
        self.start = start if start else datetime.datetime.utcnow()
        self.end = end
        self.state = state
        self.launch_id = launch_id

    @recursive_serialize
    def to_dict(self):
        return {'fworker': self.fworker, 'fw_id': self.fw_id, 'action': self.action, 'start': self.start,
                'end': self.end, 'host': self.host, 'ip': self.ip, 'launch_dir': self.launch_dir, 'state': self.state,
                'launch_id': self.launch_id}

    @property
    def time_secs(self):
        return (self.end - self.start).total_seconds() if self.end else None

    def to_db_dict(self):
        m_d = self.to_dict()
        m_d['time_secs'] = self.time_secs
        return m_d

    @classmethod
    def from_dict(cls, m_dict):
        fworker = FWorker.from_dict(m_dict['fworker'])
        action = FWAction.from_dict(m_dict['action']) if m_dict.get('action') else None
        return Launch(fworker, m_dict['fw_id'], m_dict['host'], m_dict['ip'], m_dict['launch_dir'],
                      action, m_dict['start'], m_dict['end'], m_dict['state'], m_dict['launch_id'])