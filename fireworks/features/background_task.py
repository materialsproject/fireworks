# coding: utf-8

from __future__ import unicode_literals

from fireworks.utilities.fw_serializers import FWSerializable, recursive_serialize, serialize_fw, \
    recursive_deserialize

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2014, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 10, 2014'


class BackgroundTask(FWSerializable, object):
    _fw_name = 'BackgroundTask'

    def __init__(self, tasks, num_launches=0, sleep_time=60, run_on_finish=False):
        """
        Args:
            tasks [FireTask]: a list of FireTasks to perform
            num_launches (int): the total number of times to run the process (0=infinite)
            sleep_time (int): sleep time in seconds between background runs
            run_on_finish (bool): always run this task upon completion of Firework
        """
        self.tasks = tasks if isinstance(tasks, (list, tuple)) else [tasks]
        self.num_launches = num_launches
        self.sleep_time = sleep_time
        self.run_on_finish = run_on_finish

    @recursive_serialize
    @serialize_fw
    def to_dict(self):
        return {'tasks': self.tasks, 'num_launches': self.num_launches,
                'sleep_time': self.sleep_time, 'run_on_finish': self.run_on_finish}

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        return BackgroundTask(m_dict['tasks'], m_dict['num_launches'],
                              m_dict['sleep_time'], m_dict['run_on_finish'])
