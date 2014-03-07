#!/usr/bin/env python

"""
TODO: Modify module doc.
"""

from __future__ import division

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__date__ = "3/6/14"


from fireworks.core.firework import FireTaskBase, FWAction
from fireworks.utilities.fw_utilities import explicit_serialize


@explicit_serialize
class DummyTask(FireTaskBase):

    def run_task(self, fw_spec):
        data = fw_spec["_fw_env"].get("hello", "hello")
        return FWAction(stored_data={"data": data})