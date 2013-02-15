#!/usr/bin/env python

'''
TODO: add docs
'''


__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 15, 2013'


class TaskBase():
    '''
    TODO: add docs
    '''
    
    def init(self, parameters):
        self.parameters = parameters
        
    def register_lp(self, launchpad):
        self.launchpad = launchpad
    
    # TODO: add previous outputs and FireWork to this?
    def run_task(self, fw, previous_output):
        '''
        returns an output
        :param fw:
        :param previous_output:
        '''
        raise NotImplementedError('Need to implement run_task!')
    
    # TODO: add a write to log method
    
# TODO: Task for committing a file to DB?
# TODO: add checkpoint function