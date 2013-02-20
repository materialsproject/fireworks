#!/usr/bin/env python

"""
TODO: add docs
"""
import simplejson as json

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'


class Rocket():
    """
    The Rocket fetches a workflow step from the FireWorks database and executes it.
    """
    
    def __init__(self, launchpad, fworker):
        """
        
        :param launchpad: A LaunchPad object for interacting with the FW database
        :param fworker: A FWorker object describing the computing resource
        """
        self.launchpad = launchpad
        self.fworker = fworker
    
    def run(self):
        """
        Run the rocket (actually check out a job from the database and execute it)
        """
        
        lp = self.launchpad
        
        # check a FW job out of the launchpad
        m_fw, launch_id = lp._checkout_fw(self.fworker)
        if not m_fw:
            raise ValueError("No FireWorks are ready to run and match query! {}".format(self.fworker.query))
        
        with open('fw.json', 'w') as f:
            f.write(json.dumps(m_fw.to_dict()))
        
        # execute the script inside the spec
        # TODO: support lists, native Python code, bind monitors, etc...
        # add fw_dict stuff
        # add checkpoint stuff
        # add heartbeat
        # lots of stuff to add!
        
        for my_task in m_fw.tasks:
            m_decision = my_task.run_task(m_fw)

        # TODO: continue on to next script if:
        # - it exists
        # - no fw_output.json
        # no output dict()

        # TODO: add more useful information in the launch!

        # perform finishing operation
        print 'yay'
        lp._complete_launch(m_fw, launch_id)
