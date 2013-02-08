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
    
    def __init__(self, fw_spec, fw_id=None, launch_data=None):
        '''
        
        :param fw_spec:
        '''
        self.fw_spec = fw_spec
        self.fw_id = fw_id
        self.launch_data = launch_data if launch_data else []
    
    def to_dict(self):
        return {'fw_spec': self.fw_spec, 'fw_id': self.fw_id, 'launch_data': self.launch_data}
    
    def to_db_dict(self):
        m_dict = self.to_dict()
        m_dict['state'] = self.state
        return m_dict
    
    @classmethod
    def from_dict(self, m_dict):
        return FireWork(m_dict['fw_spec'], m_dict['fw_id'], m_dict['launch_data'])
    
    @property
    def state(self):
        if len(self.launch_data) == 0:
            return "created"
        
        return "running/completed"


if __name__ == '__main__':
    fw_spec = {'_script': 'echo "howdy, your job launched successfully!" >> howdy.txt'}
    fw = FireWork(fw_spec)
    fw.to_file("fw_test.yaml")