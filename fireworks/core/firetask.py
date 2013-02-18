#!/usr/bin/env python

"""
TODO: add docs
"""
from fireworks.utilities.fw_serializers import serialize_fw


__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 15, 2013'


class FireTaskBase():
    """
    TODO: add docs
    """
    
    def __init__(self, parameters):
        # Add the following line to your FireTasks to get to_dict to work
        self.parameters = parameters
    
    # TODO: register fw_id?
    def register_lp(self, launchpad):
        self.launchpad = launchpad
    
    def run_task(self, fw):
        raise NotImplementedError('Need to implement run_task!')
    
    @serialize_fw
    def to_dict(self):
        return {"parameters": self.parameters}
    
    @classmethod
    def from_dict(self, m_dict):
        return self(m_dict['parameters'])
    
    # TODO: add a write to log method
    
# TODO: Task for committing a file to DB?
# TODO: add checkpoint function