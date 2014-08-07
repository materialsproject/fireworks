#!/usr/bin/env python

from __future__ import division

__author__ = "Bharat Medasani"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Bharat Medasani"
__email__ = "mbkumar@gmail.com"
__date__ = "7/01/14"

import unittest
import os

from fireworks import FireWork, Workflow, LaunchPad
from fireworks.user_objects.firetasks.script_task import ScriptTask



class LaunchPadTest(unittest.TestCase):

    def test_autoload(self):
        lp = LaunchPad.auto_load()
        self.assertIsInstance(lp,LaunchPad)

        LP_LOC = os.path.join(os.path.dirname(__file__),'launchpad.yaml')
        #print LP_LOC
        lp = LaunchPad.from_file(LP_LOC)
        self.assertIsInstance(lp,LaunchPad)

    def test_dict(self):
        LP_LOC = os.path.join(os.path.dirname(__file__),'launchpad.yaml')
        lp = LaunchPad.from_file(LP_LOC)
        lp_dict = lp.to_dict()
        new_lp = LaunchPad.from_dict(lp_dict)
        self.assertIsInstance(new_lp, LaunchPad)

    def test_reset(self):
        # Store some test fireworks
        # Atempt couple of ways to reset the lp and check
        lp = LaunchPad.auto_load()
        fw = FireWork(ScriptTask.from_str('echo "hello"'), name="hello")
        wf = Workflow([fw], name='test_workflow')
        lp.add_wf(wf)
        lp.reset('',require_password=False)
        fw = lp.get_fw_ids()
        wf = lp.get_wf_ids()
        self.assertFalse(fw)
        self.assertFalse(wf)

        fw = FireWork(ScriptTask.from_str('echo "hello"'), name="hello")
        lp.add_wf(fw)
        args = ('',)
        self.assertRaises(ValueError,lp.reset,*args)

    def test_add_wf(self):
        lp = LaunchPad.auto_load()
        lp.reset('',require_password=False)
        fw = FireWork(ScriptTask.from_str('echo "hello"'), name="hello")
        lp.add_wf(fw)
        wf = lp.get_wf_ids()
        self.assertTrue(wf)
        fw2 = FireWork(ScriptTask.from_str('echo "goodbye"'), name="goodbye")
        wf = Workflow([fw, fw2], name='test_workflow')
        lp.add_wf(wf)
        fw = lp.get_fw_ids()
        self.assertTrue(fw)
        lp.reset('',require_password=False)

    def test_get_launch_by_id(self):
        pass
    def test_get_fw_by_id(self):
        pass
    def test_get_wf_by_fw_id(self):
        pass
    def test_get_fw_ids(self):
        pass
    def test_defuse_fw(self):
        pass
    def test_reignite_fw(self):
        pass
    def test_defuse_wf(self):
        pass
    def test_reignite_wf(self):
        pass
    def test_archive_wf(self):
        pass
    def test_reserve_fw(self):
        pass


if __name__ == '__main__':
    unittest.main()
