#!/usr/bin/env python

from fireworks.core.firework import FWAction, FiretaskBase

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 17, 2013'


class AdditionTask(FiretaskBase):
    _fw_name = "Addition Task"

    def run_task(self, fw_spec):
        input_array = fw_spec['input_array']
        m_sum = sum(input_array)

        print("The sum of {} is: {}".format(input_array, m_sum))

        return FWAction(stored_data={'sum': m_sum},
                        mod_spec=[{'_push': {'input_array': m_sum}}])
