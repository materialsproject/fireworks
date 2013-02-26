#!/usr/bin/env python

"""
TODO: add docs
"""
from fireworks.core.firetask import FireTaskBase
from fireworks.utilities.fw_serializers import FWSerializable
from fireworks.core.firework import FireWork, FWDecision, WFConnections, FWorkflow

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 25, 2013'


class AddModifyTask(FireTaskBase, FWSerializable):

    _fw_name = "Add and Modify Task"

    def run_task(self, fw):
        input_array = fw.spec['input_array']
        m_sum = sum(input_array)

        print "The sum of {} is: {}".format(input_array, m_sum)

        # store the sum; push the sum to the input array of the next sum
        return FWDecision('MODIFY', {'sum': m_sum}, {'dict_mods': [{'_push': {'input_array': m_sum}}]})

