#!/usr/bin/env python

'''
TODO: add docs
'''
from fireworks.utilities.fw_serializers import FWSerializable


__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 5, 2013"


class FireWork(FWSerializable):
    
    _fw_name = "FireWork"
    
    def __init__(self, fw_spec):
        '''
        
        :param fw_spec:
        '''
        self.fw_spec = fw_spec
    
    def to_dict(self):
        return {'fw_spec': self.fw_spec}
    
    def from_dict(self, m_dict):
        return FireWork(m_dict['fw_spec'])