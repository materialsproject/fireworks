#!/usr/bin/env python

"""
TODO: add docs
"""
import datetime
from fireworks.core.fw_constants import LAUNCH_RANKS
from fireworks.core.fworker import FWorker
from fireworks.utilities.fw_serializers import serialize_fw, FWSerializable, recursive_serialize, recursive_deserialize


__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 15, 2013'


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

        # TODO: add a write to log method

        # TODO: Task for committing a file to DB?
        # TODO: add checkpoint function


class FWAction():
    """
    TODO: add docs

    """
    # TODO: ADDIFY can be merged into ADD (definitely)
    # TODO: DETOUR can be merged into ADD (probably)

    commands = ['CONTINUE', 'DEFUSE', 'MODIFY', 'DETOUR', 'CREATE', 'ADDIFY', 'PHOENIX', 'BREAK']

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