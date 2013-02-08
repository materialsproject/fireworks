#!/usr/bin/env python

'''
TODO: add docs
'''
import subprocess
import os

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'


class Rocket():
    
    def __init__(self, launchpad, fworker):
        self.lp = launchpad
        self.fworker = fworker
    
    def run(self):
        
        # check a FW job out of the launchpad
        
        # TODO: actually check it out
        fw_id = self.lp.get_fw_ids()[0]
        m_fw = self.lp.get_fw_by_id(fw_id)
        
        print m_fw.fw_spec
        
        # execute the spec
        cmd = m_fw.fw_spec['_script']
        
        if isinstance(cmd, basestring):
            os.system(cmd)

        # add subprocess stuff
        
        # add fw_dict stuff
        
        
        # perform finishing operations