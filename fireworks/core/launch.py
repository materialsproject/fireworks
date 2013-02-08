#!/usr/bin/env python

'''
TODO: add docs
'''


__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 8, 2013'

# TODO: add log


class Launch():
    
    def __init__(self, worker, l_id=None, state=None):
        self.worker = worker
        self.l_id = l_id
        self.state = state
