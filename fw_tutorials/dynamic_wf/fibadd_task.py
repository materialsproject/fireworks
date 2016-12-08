#!/usr/bin/env python

from fireworks.core.firework import FWAction, Firework, FiretaskBase

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 25, 2013'


class FibonacciAdderTask(FiretaskBase):

    _fw_name = "Fibonacci Adder Task"

    def run_task(self, fw_spec):
        smaller = fw_spec['smaller']
        larger = fw_spec['larger']
        stop_point = fw_spec['stop_point']

        m_sum = smaller + larger
        if m_sum < stop_point:
            print('The next Fibonacci number is: {}'.format(m_sum))
            # create a new Fibonacci Adder to add to the workflow
            new_fw = Firework(FibonacciAdderTask(), {'smaller': larger, 'larger': m_sum, 'stop_point': stop_point})
            return FWAction(stored_data={'next_fibnum': m_sum}, additions=new_fw)

        else:
            print('We have now exceeded our limit; (the next Fibonacci number would have been: {})'.format(m_sum))
            return FWAction()

