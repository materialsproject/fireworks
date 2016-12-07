#!/usr/bin/env python

from fireworks.core.firework import FiretaskBase, FWAction

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 25, 2013'


class AddModifyTask(FiretaskBase):

    _fw_name = "Add and Modify Task"

    def run_task(self, fw_spec):
        input_array = fw_spec['input_array']
        m_sum = sum(input_array)

        print("The sum of {} is: {}".format(input_array, m_sum))

        # store the sum; push the sum to the input array of the next sum
        return FWAction(stored_data={'sum': m_sum}, mod_spec=[{'_push': {'input_array': m_sum}}])
