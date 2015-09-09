#!/usr/bin/env python

from fireworks.core.firework import FWAction, Firework, FireTaskBase

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2015, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Sept 8, 2015'


class PrintJobTask(FireTaskBase):

    _fw_name = "Print Job Task"

    def run_task(self, fw_spec):
        job_info_array = fw_spec['_job_info']
        prev_job_info = job_info_array[-1]

        print('The name of the previous job was: {}'.format(prev_job_info['name']))
        print('The id of the previous job was: {}'.format(prev_job_info['fw_id']))
        print('The location of the previous job was: {}'.format(prev_job_info['launch_dir']))


