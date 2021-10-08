#!/usr/bin/env python

from fireworks.core.firework import FiretaskBase, Firework, FWAction

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 25, 2013"


class FibonacciAdderTask(FiretaskBase):

    _fw_name = "Fibonacci Adder Task"

    def run_task(self, fw_spec):
        smaller = fw_spec["smaller"]
        larger = fw_spec["larger"]
        stop_point = fw_spec["stop_point"]

        m_sum = smaller + larger
        if m_sum < stop_point:
            print(f"The next Fibonacci number is: {m_sum}")
            # create a new Fibonacci Adder to add to the workflow
            new_fw = Firework(FibonacciAdderTask(), {"smaller": larger, "larger": m_sum, "stop_point": stop_point})
            return FWAction(stored_data={"next_fibnum": m_sum}, additions=new_fw)

        else:
            print(f"We have now exceeded our limit; (the next Fibonacci number would have been: {m_sum})")
            return FWAction()
