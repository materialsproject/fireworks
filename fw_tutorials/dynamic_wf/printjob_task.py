#!/usr/bin/env python

from fireworks.core.firework import FiretaskBase

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2015, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Sept 8, 2015"


class PrintJobTask(FiretaskBase):

    _fw_name = "Print Job Task"

    def run_task(self, fw_spec):
        job_info_array = fw_spec["_job_info"]
        prev_job_info = job_info_array[-1]

        print(f"The name of the previous job was: {prev_job_info['name']}")
        print(f"The id of the previous job was: {prev_job_info['fw_id']}")
        print(f"The location of the previous job was: {prev_job_info['launch_dir']}")
