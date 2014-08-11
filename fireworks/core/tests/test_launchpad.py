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

from fireworks import FireWork, Workflow, LaunchPad, FWorker
from fireworks.core.rocket_launcher import rapidfire
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
        lp = LaunchPad.auto_load()
        lp.reset('',require_password=False)

        # define the individual FireWorks used in the Workflow
        # Parent Firework
        fw_p = FireWork(ScriptTask.from_str('echo "Cronus is the ruler of titans"'), name="parent")
        # Sibling fireworks
        fw_s1 = FireWork(ScriptTask.from_str('echo "Zeus is son of Cronus"'), name="sib1")
        fw_s2 = FireWork(ScriptTask.from_str('echo "Poisedon is brother of Zeus"'), name="sib2")
        fw_s3 = FireWork(ScriptTask.from_str('echo "Hades is brother of Zeus"'), name="sib3")
        fw_s4 = FireWork(ScriptTask.from_str('echo "Demeter is sister & wife of Zeus"'), name="sib4")
        fw_s5 = FireWork(ScriptTask.from_str('echo "Lapetus is son of Oceanus"'), name="cousin1")
        # Children fireworks
        fw_c1 = FireWork(ScriptTask.from_str('echo "Ares is son of Zeus"'), name="c1")
        fw_c2 = FireWork(ScriptTask.from_str('echo "Persephone is daughter of Zeus & Demeter and wife of Hades"'), name="c2")
        fw_c3 = FireWork(ScriptTask.from_str('echo "Makaria is daughter of Hades & Persephone"'), name="c3")
        fw_c4 = FireWork(ScriptTask.from_str('echo "Dione is descendant of Lapetus"'), name="c4")
        fw_c5 = FireWork(ScriptTask.from_str('echo "Aphrodite is son of of Zeus and Dione"'), name="c5")
        fw_c6 = FireWork(ScriptTask.from_str('echo "Atlas is son of of Lapetus"'), name="c6")
        fw_c7 = FireWork(ScriptTask.from_str('echo "Maia is daughter of Atlas"'), name="c7")
        fw_c8 = FireWork(ScriptTask.from_str('echo "Hermes is daughter of Maia and Zeus"'), name="c8")


        # assemble Workflow from FireWorks and their connections by id
        workflow = Workflow([fw_p,fw_s1,fw_s2,fw_s3,fw_s4,fw_s5,fw_c1,fw_c2,fw_c3,fw_c4,fw_c5,fw_c6,fw_c7,fw_c8],
                            {fw_p: [fw_s1,fw_s2,fw_s3,fw_s4],
                             fw_s1: [fw_c1,fw_c2,fw_c5,fw_c8],
                             fw_s3: [fw_c3],
                             fw_s4: [fw_c2],
                             fw_s5: [fw_c4, fw_c6],
                             fw_c2: [fw_c3],
                             fw_c4: [fw_c5],
                             fw_c6: [fw_c7],
                             fw_c7: [fw_c8]})

        # store workflow
        lp.add_wf(workflow)

        # defuse Zeus
        zeus_fw_id = lp.get_fw_ids({'name':'sib1'},limit=1)[0]
        c1_fw_id = lp.get_fw_ids({'name':'c1'},limit=1)[0]
        c2_fw_id = lp.get_fw_ids({'name':'c2'},limit=1)[0]
        c3_fw_id = lp.get_fw_ids({'name':'c3'},limit=1)[0]
        c5_fw_id = lp.get_fw_ids({'name':'c5'},limit=1)[0]
        c8_fw_id = lp.get_fw_ids({'name':'c8'},limit=1)[0]
        print zeus_fw_id
        print c1_fw_id
        print c2_fw_id
        print c3_fw_id
        print c5_fw_id
        print c8_fw_id
        lp.defuse_fw(zeus_fw_id)

        defused_ids = lp.get_fw_ids({'state':'DEFUSED'})
        self.assertIn(zeus_fw_id,defused_ids)
        #self.assertIn(c1_fw_id,defused_ids)
        #self.assertIn(c2_fw_id,defused_ids)
        #self.assertIn(c3_fw_id,defused_ids)
        #self.assertIn(c5_fw_id,defused_ids)
        #self.assertIn(c8_fw_id,defused_ids)

        # Run remaining fireworks
        rapidfire(lp, FWorker())

        # Ensure except for Zeus and his children, all other fw are run
        completed_ids = lp.get_fw_ids({'state':'COMPLETED'})
        # Check for the state of Lapetus and his descendants
        s5_fw_id = lp.get_fw_ids({'name':'cousin1'},limit=1)[0]
        c7_fw_id = lp.get_fw_ids({'name':'c7'},limit=1)[0]
        c6_fw_id = lp.get_fw_ids({'name':'c6'},limit=1)[0]
        c4_fw_id = lp.get_fw_ids({'name':'c4'},limit=1)[0]
        fw = lp.get_fw_by_id(s5_fw_id)
        print fw.to_dict
        self.assertIn(s5_fw_id,completed_ids)
        self.assertIn(c7_fw_id,completed_ids)
        self.assertIn(c6_fw_id,completed_ids)
        self.assertIn(c4_fw_id,completed_ids)
        # Check for the state of Zeus siblings
        s2_fw_id = lp.get_fw_ids({'name':'sib2'},limit=1)[0]
        s3_fw_id = lp.get_fw_ids({'name':'sib3'},limit=1)[0]
        s4_fw_id = lp.get_fw_ids({'name':'sib4'},limit=1)[0]
        self.assertIn(s2_fw_id,completed_ids)
        self.assertIn(s3_fw_id,completed_ids)
        self.assertIn(s4_fw_id,completed_ids)
        # Check for the state of Zeus parent
        par_fw_id = lp.get_fw_ids({'name':'parent'},limit=1)[0]
        self.assertIn(par_fw_id,completed_ids)
        # Check for the status of Zeus children
        defused_ids = lp.get_fw_ids({'state':'DEFUSED'})
        self.assertIn(c1_fw_id,defused_ids)
        self.assertIn(c2_fw_id,defused_ids)
        self.assertIn(c3_fw_id,defused_ids)
        self.assertIn(c5_fw_id,defused_ids)
        self.assertIn(c8_fw_id,defused_ids)
        #fw = lp.get_fw_by_id(c1_fw_id)
        #print fw.state, fw.name
        #wf = lp.get_wf_by_fw_id(s5_fw_id)
        #print wf

        #lp.reset('',require_password=False)
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
