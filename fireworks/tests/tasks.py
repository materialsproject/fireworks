# coding: utf-8

from __future__ import unicode_literals, division

"""
TODO: Modify module doc.
"""


__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__date__ = "3/6/14"


from fireworks.core.firework import FiretaskBase, FWAction
from fireworks.utilities.fw_utilities import explicit_serialize


@explicit_serialize
class DummyFWEnvTask(FiretaskBase):

    def run_task(self, fw_spec):
        data = fw_spec["_fw_env"].get("hello", "hello")
        return FWAction(stored_data={"data": data})


@explicit_serialize
class DummyJobPassTask(FiretaskBase):

    def run_task(self, fw_spec):
        return FWAction(stored_data={"data": fw_spec['_job_info']})

@explicit_serialize
class DummyLPTask(FiretaskBase):

    def run_task(self, fw_spec):
        return FWAction(stored_data={"fw_id": self.fw_id, "host": self.launchpad.host})