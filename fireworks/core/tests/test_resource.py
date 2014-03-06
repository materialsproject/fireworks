__author__ = 'Shyue Ping Ong'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Shyue Ping Ong'
__email__ = 'ongsp@ucsd.edu'
__date__ = '3/6/14'

import unittest

from fireworks.core.firework import FireTaskBase
from fireworks.core.resource import ResourceBase, supported_resources, FWResourceError


class Localhost(ResourceBase):

    env = {"hello": "world", "me.1": "me.2"}

    @classmethod
    def at_resource(self):
        return True


class Invalidresource(ResourceBase):

    env = {"hello": "world"}

    @classmethod
    def at_resource(self):
        return False


@supported_resources(Localhost)
class DummyTask(FireTaskBase):

    def run_task(self, fw_spec):
        return self["_fw_resource"]["hello"]


@supported_resources(Invalidresource)
class DummyTask2(FireTaskBase):

    def run_task(self, fw_spec):
        return self["_fw_resource"]["hello"]


@supported_resources(Localhost)
class DummyTask3(FireTaskBase):

    def run_task(self, fw_spec):
        return self["_fw_resource"].hello


class ResourceSettingsTest(unittest.TestCase):

    def test_init(self):
        fw = DummyTask()
        self.assertEqual(fw.run_task({}), "world")
        self.assertRaises(FWResourceError, DummyTask2)
        fw = DummyTask3()
        self.assertEqual(fw.run_task({}), "world")

if __name__ == '__main__':
    unittest.main()
