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
    '''
    The Rocket fetches a workflow step from the FireWorks database and executes it.
    '''
    
    def __init__(self, launchpad, fworker):
        '''
        
        :param launchpad: A LaunchPad object for interacting with the FW database
        :param fworker: A FWorker object describing the computing resource
        '''
        self.launchpad = launchpad
        self.fworker = fworker
    
    def run(self):
        
        lp = self.launchpad
        
        # check a FW job out of the launchpad
        m_fw, launch_id = lp._checkout_fw(self.fworker)
        if not m_fw:
            raise ValueError("No FireWorks are ready to run and match query! {}".format(self.fworker.query))
        
        # TODO: write the spec to a file in the directory
        # TODO: write the entire FireWork?
        with open('fw_json.spec', 'w') as f:
            f.write(json.dumps(m_fw.fw_spec))
        
        # execute the script inside the spec
        # TODO: support lists, native Python code, bind monitors, etc...
        # add subprocess stuff'
        # TODO: hook into os.system if possible, else use shutil or subprocess
        # add fw_dict stuff
        # add monitoring stuff
        # lots of stuff to add!
        cmd = m_fw.fw_spec['_script']
        if isinstance(cmd, basestring):
            os.system(cmd)

        # perform finishing operation
        lp._complete_launch(m_fw, launch_id)
