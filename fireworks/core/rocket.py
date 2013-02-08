#!/usr/bin/env python

'''
TODO: add docs
'''
import simplejson as json
import os

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'


class Rocket():
    
    def __init__(self, launchpad, fworker):
        self.launchpad = launchpad
        self.fworker = fworker
    
    def run(self):
        
        query = self.fworker.query
        lp = self.launchpad
        
        # check a FW job out of the launchpad
        
        (m_fw, launch_id) = lp._checkout_fw(query)
        if not m_fw:
            raise ValueError("No jobs matching query! {}".format(query))
        
        # TODO: write the spec to a file in the directory
        with open('fw_json.spec', 'w') as f:
            f.write(json.dumps(m_fw.fw_spec))
        
        # execute the script inside the spec
        # TODO: support lists, native Python code, bind monitors, etc...
        # add subprocess stuff
        # add fw_dict stuff
        cmd = m_fw.fw_spec['_script']
        if isinstance(cmd, basestring):
            os.system(cmd)

        # perform finishing operation
        lp._complete_launch(m_fw, launch_id)
