# coding: utf-8

from __future__ import unicode_literals, division

"""
TODO: Modify unittest doc.
"""


__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__date__ = "2/26/14"

import unittest

from fireworks.core.firework import Firework, Workflow, FireTaskBase
from fireworks.user_objects.firetasks.script_task import PyTask


class FireTaskBaseTest(unittest.TestCase):

    def test_init(self):
        class DummyTask(FireTaskBase):

            required_params = ["hello"]

            def run_task(self, fw_spec):
                return self["hello"]

        self.assertRaises(ValueError, DummyTask)
        d = DummyTask(hello="world")
        self.assertEqual(d.run_task({}), "world")
        d = DummyTask({"hello": "world2"})
        self.assertEqual(d.run_task({}), "world2")

        class DummyTask2(FireTaskBase):

            pass

        d = DummyTask2()
        self.assertRaises(NotImplementedError, d.run_task, {})


class WorkflowTest(unittest.TestCase):

    def test_init(self):

        fws = []
        for i in range(5):
            fw = Firework([PyTask(func="print", args=[i])], fw_id=i)
            fws.append(fw)
        wf = Workflow(fws, links_dict={0: [1, 2, 3], 1: [4], 2: [4]})
        self.assertIsInstance(wf, Workflow)
        self.assertRaises(ValueError, Workflow, fws,
                          links_dict={0: [1, 2, 3], 1: [4], 100: [4]})
        self.assertRaises(ValueError, Workflow, fws,
                          links_dict={0: [1, 2, 3], 1: [4], 2: [100]})


if __name__ == '__main__':
    unittest.main()
