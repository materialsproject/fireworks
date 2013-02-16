#!/usr/bin/env python

'''
TODO: add docs
'''
import simplejson as json
from fireworks.core.firetask import SubprocessTask

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
        '''
        Run the rocket (actually check out a job from the database and execute it)
        '''
        
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
        # add fw_dict stuff
        # add checkpoint stuff
        # add heartbeat
        # lots of stuff to add!
        cmd = m_fw.fw_spec['_script']
        my_task = None
        if isinstance(cmd, basestring):
            # run a subprocess command using the shell
            my_task = SubprocessTask({"script": cmd, "use_shell": True})
        
        my_task.register_lp(lp)  # TODO: is this really needed?
        my_task.run_task(m_fw, {})
        
        # TODO: add the output of the task from run_task
        
        # perform finishing operation
        lp._complete_launch(m_fw, launch_id)
