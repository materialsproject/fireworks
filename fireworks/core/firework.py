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
    
    def __init__(self, fw_spec, fw_id=None):
        '''
        
        :param fw_spec:
        '''
        self.fw_spec = fw_spec
        self.fw_id = fw_id
    
    def to_dict(self):
        return {'fw_spec': self.fw_spec, 'fw_id': self.fw_id}
    
    @classmethod
    def from_dict(self, m_dict):
        return FireWork(m_dict['fw_spec'], m_dict['fw_id'])


if __name__ == '__main__':
    fw_spec = {'_script': 'echo "howdy, your job launched successfully!" >> howdy.txt'}
    fw = FireWork(fw_spec)
    fw.to_file("fw_test.yaml")