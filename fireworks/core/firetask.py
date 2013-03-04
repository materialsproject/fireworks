#!/usr/bin/env python

"""
TODO: add docs
"""
from fireworks.utilities.fw_serializers import serialize_fw, FWSerializable
from fireworks.utilities.fw_utilities import recursive_dict


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
    def to_dict(self):
        return {"parameters": self.parameters}

    @classmethod
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

    def to_dict(self):
        return {"action": self.command, "stored_data": self.stored_data, "mod_spec": recursive_dict(self.mod_spec)}

    @classmethod
    def from_dict(cls, m_dict):
        return FWAction(m_dict['action'], m_dict['stored_data'], m_dict['mod_spec'])