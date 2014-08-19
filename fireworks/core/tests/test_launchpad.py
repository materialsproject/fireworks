#!/usr/bin/env python

from __future__ import division

__author__ = "Bharat Medasani"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Bharat Medasani"
__email__ = "mbkumar@gmail.com"
__date__ = "7/01/14"

import unittest
import time
import os
import glob
import shutil
import datetime
from multiprocessing import Process

from fireworks import FireWork, Workflow, LaunchPad, FWorker
from fw_tutorials.dynamic_wf.addmod_task import AddModifyTask
from fireworks.core.rocket_launcher import rapidfire, launch_rocket
from fireworks.user_objects.firetasks.script_task import ScriptTask, PyTask

TESTDB_NAME = 'fireworks_unittest'
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class LaunchPadTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lp = None
        cls.fworker = FWorker()
        try:
            cls.lp = LaunchPad(name=TESTDB_NAME, strm_lvl='ERROR')
            cls.lp.reset(password=None, require_password=False)
        except:
            raise unittest.SkipTest('MongoDB is not running in localhost:27017! Skipping tests.')

    @classmethod
    def tearDownClass(cls):
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

    def setUp(self):
        self.old_wd = os.getcwd()
        self.LP_LOC = os.path.join(MODULE_DIR,'launchpad.yaml')
        self.lp.to_file(self.LP_LOC)


    def tearDown(self):
        self.lp.reset(password=None,require_password=False)
        # Delete launch locations
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        os.chdir(self.old_wd)
        for ldir in glob.glob(os.path.join(MODULE_DIR,"launcher_*")):
            shutil.rmtree(ldir)

        if os.path.exists(self.LP_LOC):
            os.remove(self.LP_LOC)

    def test_dict_from_file(self):
        lp = LaunchPad.from_file(self.LP_LOC)
        lp_dict = lp.to_dict()
        new_lp = LaunchPad.from_dict(lp_dict)
        self.assertIsInstance(new_lp, LaunchPad)

    def test_reset(self):
        # Store some test fireworks
        # Atempt couple of ways to reset the lp and check
        fw = FireWork(ScriptTask.from_str('echo "hello"'), name="hello")
        wf = Workflow([fw], name='test_workflow')
        self.lp.add_wf(wf)
        self.lp.reset('',require_password=False)
        self.assertFalse(self.lp.get_fw_ids())
        self.assertFalse(self.lp.get_wf_ids())

    def test_pw_check(self):
        fw = FireWork(ScriptTask.from_str('echo "hello"'), name="hello")
        self.lp.add_wf(fw)
        args = ('',)
        self.assertRaises(ValueError,self.lp.reset, *args)

    def test_add_wf(self):
        fw = FireWork(ScriptTask.from_str('echo "hello"'), name="hello")
        self.lp.add_wf(fw)
        wf = self.lp.get_wf_ids()
        self.assertTrue(wf)  # TODO: assertTrue is very sloppy. Check for something specific and meaningful, e.g. a count
        fw2 = FireWork(ScriptTask.from_str('echo "goodbye"'), name="goodbye")
        wf = Workflow([fw, fw2], name='test_workflow')
        self.lp.add_wf(wf)
        fw = self.lp.get_fw_ids()
        self.assertTrue(fw) # TODO: assertTrue is very sloppy. Check for something specific and meaningful, e.g. a count
        self.lp.reset('',require_password=False)


class LaunchPadDefuseReigniteRerunArchiveDeleteTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lp = None
        cls.fworker = FWorker()
        try:
            cls.lp = LaunchPad(name=TESTDB_NAME, strm_lvl='ERROR')
            cls.lp.reset(password=None, require_password=False)
        except:
            raise unittest.SkipTest('MongoDB is not running in localhost:27017! Skipping tests.')

    @classmethod
    def tearDownClass(cls):
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

    def setUp(self):
        # define the individual FireWorks used in the Workflow
        # Parent Firework
        fw_p = FireWork(ScriptTask.from_str(
            'echo "Cronus is the ruler of titans"',
            {'store_stdout':True}), name="parent", fw_id=1)
        # Sibling fireworks
        fw_s1 = FireWork(ScriptTask.from_str(
            'echo "Zeus is son of Cronus"',
            {'store_stdout':True}), name="sib1", fw_id=2, parents=fw_p)
        fw_s2 = FireWork(ScriptTask.from_str(
            'echo "Poisedon is brother of Zeus"',
            {'store_stdout':True}), name="sib2", fw_id=3, parents=fw_p)
        fw_s3 = FireWork(ScriptTask.from_str(
            'echo "Hades is brother of Zeus"',
            {'store_stdout':True}), name="sib3", fw_id=4, parents=fw_p)
        fw_s4 = FireWork(ScriptTask.from_str(
            'echo "Demeter is sister & wife of Zeus"',
            {'store_stdout':True}), name="sib4", fw_id=5, parents=fw_p)
        fw_s5 = FireWork(ScriptTask.from_str(
            'echo "Lapetus is son of Oceanus"',
            {'store_stdout':True}), name="cousin1", fw_id=6)
        # Children fireworks
        fw_c1 = FireWork(ScriptTask.from_str(
            'echo "Ares is son of Zeus"',
            {'store_stdout':True}), name="c1", fw_id=7, parents=fw_s1)
        fw_c2 = FireWork(ScriptTask.from_str(
            'echo "Persephone is daughter of Zeus & Demeter and wife of Hades"',
            {'store_stdout':True}), name="c2", fw_id=8, parents=[fw_s1,fw_s4])
        fw_c3 = FireWork(ScriptTask.from_str(
            'echo "Makaria is daughter of Hades & Persephone"',
            {'store_stdout':True}), name="c3", fw_id=9, parents=[fw_s3,fw_c2])
        fw_c4 = FireWork(ScriptTask.from_str(
            'echo "Dione is descendant of Lapetus"',
            {'store_stdout':True}), name="c4", fw_id=10, parents=fw_s5)
        fw_c5 = FireWork(ScriptTask.from_str(
            'echo "Aphrodite is son of of Zeus and Dione"',
            {'store_stdout':True}), name="c5", fw_id=11, parents=[fw_s1,fw_c4])
        fw_c6 = FireWork(ScriptTask.from_str(
            'echo "Atlas is son of of Lapetus"',
            {'store_stdout':True}), name="c6", fw_id=12,parents=fw_s5)
        fw_c7 = FireWork(ScriptTask.from_str(
            'echo "Maia is daughter of Atlas"',
            {'store_stdout':True}), name="c7", fw_id=13, parents=fw_c6)
        fw_c8 = FireWork(ScriptTask.from_str(
            'echo "Hermes is daughter of Maia and Zeus"',
            {'store_stdout':True}), name="c8", fw_id=14, parents=[fw_s1,fw_c7])


        # assemble Workflow from FireWorks and their connections by id
        workflow = Workflow([fw_p,fw_s1,fw_s2,fw_s3,fw_s4,fw_s5,fw_c1,fw_c2,
                             fw_c3,fw_c4,fw_c5,fw_c6,fw_c7,fw_c8])
        self.lp.add_wf(workflow)

        # Give names to fw_ids
        self.zeus_fw_id = 2
        self.zeus_child_fw_ids = set([7,8,9,11,14])
        self.lapetus_desc_fw_ids = set([6,10,12,13])
        self.zeus_sib_fw_ids = set([3,4,5])
        self.par_fw_id = 1
        self.all_ids = self.zeus_child_fw_ids | self.lapetus_desc_fw_ids | \
                       self.zeus_sib_fw_ids | set([self.zeus_fw_id]) | \
                       set([self.par_fw_id])

        self.old_wd = os.getcwd()

    def tearDown(self):
        self.lp.reset(password=None,require_password=False)
        # Delete launch locations
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        os.chdir(self.old_wd)
        for ldir in glob.glob(os.path.join(MODULE_DIR,"launcher_*")):
            shutil.rmtree(ldir)

    def _teardown(self, dests):
        for f in dests:
            if os.path.exists(f):
                os.remove(f)

    def test_defuse_fw(self):
        # defuse Zeus
        self.lp.defuse_fw(self.zeus_fw_id)

        defused_ids = self.lp.get_fw_ids({'state':'DEFUSED'})
        self.assertIn(self.zeus_fw_id, defused_ids)
        try:
            # Launch remaining fireworks
            rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)

            # Ensure except for Zeus and his children, all other fw are launched
            completed_ids = set(self.lp.get_fw_ids({'state':'COMPLETED'}))
            # Check that Lapetus and his descendants are subset of  completed fwids
            self.assertTrue(self.lapetus_desc_fw_ids.issubset(completed_ids))
            # Check that Zeus siblings are subset of completed fwids
            self.assertTrue(self.zeus_sib_fw_ids.issubset(completed_ids))

            # Check that Zeus and children are subset of incompleted fwids
            fws_no_run = set(self.lp.get_fw_ids({'state':{'$nin':['COMPLETED']}}))
            self.assertIn(self.zeus_fw_id,fws_no_run)
            self.assertTrue(self.zeus_child_fw_ids.issubset(fws_no_run))
        except:
            raise

    def test_defuse_fw_after_completion(self):
        # Launch rockets in rapidfire
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)
        # defuse Zeus
        self.lp.defuse_fw(self.zeus_fw_id)

        defused_ids = self.lp.get_fw_ids({'state':'DEFUSED'})
        self.assertIn(self.zeus_fw_id,defused_ids)
        completed_ids = set(self.lp.get_fw_ids({'state':'COMPLETED'}))
        self.assertFalse(self.zeus_child_fw_ids.issubset(completed_ids))

    def test_reignite_fw(self):
        # Defuse Zeus
        self.lp.defuse_fw(self.zeus_fw_id)
        defused_ids = self.lp.get_fw_ids({'state':'DEFUSED'})
        self.assertIn(self.zeus_fw_id,defused_ids)

        # Launch remaining fireworks
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)

        # Reignite Zeus and his children's fireworks and launch them
        self.lp.reignite_fw(self.zeus_fw_id)
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)

        # Check for the status of Zeus and children in completed fwids
        completed_ids = set(self.lp.get_fw_ids({'state':'COMPLETED'}))
        self.assertIn(self.zeus_fw_id,completed_ids)
        self.assertTrue(self.zeus_child_fw_ids.issubset(completed_ids))

    def test_defuse_wf(self):
        # defuse Workflow containing Zeus
        self.lp.defuse_wf(self.zeus_fw_id)
        defused_ids = self.lp.get_fw_ids({'state':'DEFUSED'})
        self.assertIn(self.zeus_fw_id,defused_ids)

        # Launch remaining fireworks
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)

        # Check for the state of all fws in Zeus workflow in incomplete fwids
        fws_no_run = set(self.lp.get_fw_ids({'state':{'$nin':['COMPLETED']}}))
        self.assertEqual(fws_no_run,self.all_ids)

    def test_defuse_wf_after_partial_run(self):
        # Run a firework before defusing Zeus
        launch_rocket(self.lp, self.fworker)

        # defuse Workflow containing Zeus
        self.lp.defuse_wf(self.zeus_fw_id)
        defused_ids = self.lp.get_fw_ids({'state':'DEFUSED'})
        self.assertIn(self.zeus_fw_id,defused_ids)

        fws_no_run = set(self.lp.get_fw_ids({'state':'COMPLETED'}))
        self.assertEqual(len(fws_no_run),0)

        # Try launching fireworks and check if any are launched
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)
        fws_no_run = set(self.lp.get_fw_ids({'state':'COMPLETED'}))
        self.assertEqual(len(fws_no_run),0)

    def test_reignite_wf(self):
        # Defuse workflow containing Zeus
        self.lp.defuse_wf(self.zeus_fw_id)
        defused_ids = self.lp.get_fw_ids({'state':'DEFUSED'})
        self.assertIn(self.zeus_fw_id,defused_ids)

        # Launch any remaining fireworks
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)

        # Reignite Zeus and his children's fireworks and launch them
        self.lp.reignite_wf(self.zeus_fw_id)
        rapidfire(self.lp, FWorker(),m_dir=MODULE_DIR)

        # Check for the status of all fireworks Zeus workflow in completed fwids
        fws_completed = set(self.lp.get_fw_ids({'state':'COMPLETED'}))
        self.assertEqual(fws_completed, self.all_ids)

    def test_archive_wf(self):
        # Run a firework before archiving Zeus
        launch_rocket(self.lp, self.fworker)

        # archive Workflow containing Zeus. Ensure all are archived
        self.lp.archive_wf(self.zeus_fw_id)
        archived_ids = set(self.lp.get_fw_ids({'state':'ARCHIVED'}))
        self.assertEqual(archived_ids, self.all_ids)

        # Try to launch the fireworks and check if any are launched
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)
        fws_completed = set(self.lp.get_fw_ids({'state':'COMPLETED'}))
        self.assertFalse(fws_completed)

        # Query for provenance
        fw = self.lp.get_fw_by_id(self.zeus_fw_id)
        self.assertTrue(fw)  # can probably do a better query than True

    def test_delete_wf(self):
        # Run a firework before deleting Zeus
        launch_rocket(self.lp, self.fworker)

        # Delete workflow containing Zeus.
        self.lp.delete_wf(self.zeus_fw_id)
        # Check if any fireworks and the workflow are available
        with self.assertRaises(ValueError):
            self.lp.get_wf_by_fw_id(self.zeus_fw_id)
        fw_ids = self.lp.get_fw_ids()
        self.assertFalse(fw_ids)
        wf_ids = self.lp.get_wf_ids()
        self.assertFalse(wf_ids)

    def test_rerun_fws2(self):
        # Launch all fireworks
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)
        fw = self.lp.get_fw_by_id(self.zeus_fw_id)
        first_ldir = fw.launches[0].launch_dir
        ts = datetime.datetime.utcnow()

        # Rerun Zeus
        self.lp.rerun_fw(self.zeus_fw_id, rerun_duplicates=True)
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)

        fw = self.lp.get_fw_by_id(self.zeus_fw_id)
        fw_start_t =  fw.launches[0].time_start
        second_ldir = fw.launches[0].launch_dir

        self.assertNotEqual(first_ldir,second_ldir)

        self.assertTrue(fw_start_t > ts)
        for fw_id in self.zeus_child_fw_ids:
            fw = self.lp.get_fw_by_id(fw_id)
            fw_start_t =  fw.launches[0].time_start
            self.assertTrue(fw_start_t > ts)
        for fw_id in self.zeus_sib_fw_ids:
            fw = self.lp.get_fw_by_id(fw_id)
            fw_start_t =  fw.launches[0].time_start
            self.assertFalse(fw_start_t > ts)


class LaunchPadLostRunsDetectTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lp = None
        cls.fworker = FWorker()
        try:
            cls.lp = LaunchPad(name=TESTDB_NAME, strm_lvl='ERROR')
            cls.lp.reset(password=None, require_password=False)
        except:
            raise unittest.SkipTest('MongoDB is not running in localhost:27017! Skipping tests.')

    @classmethod
    def tearDownClass(cls):
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

    def setUp(self):
        # Define a timed fireWork
        fw_timer = FireWork(PyTask(func='time.sleep',args=[5]), name="timer")
        self.lp.add_wf(fw_timer)

        # Get assigned fwid for timer firework
        self.fw_id = self.lp.get_fw_ids({'name':'timer'},limit=1)[0]

        self.old_wd = os.getcwd()

    def tearDown(self):
        self.lp.reset(password=None,require_password=False)
        # Delete launch locations
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        os.chdir(self.old_wd)
        for ldir in glob.glob(os.path.join(MODULE_DIR,"launcher_*")):
            shutil.rmtree(ldir)

    def test_detect_lostruns(self):
        # Launch the timed firework in a separate process
        class RocketProcess(Process):
            def __init__(self, lpad, fworker):
                super(self.__class__,self).__init__()
                self.lpad = lpad
                self.fworker = fworker

            def run(self):
                launch_rocket(self.lpad, self.fworker)

        rp = RocketProcess(self.lp, self.fworker)
        rp.start()
        time.sleep(1)   # Wait 1 sec and kill the rocket
        rp.terminate()

        fw_ids = self.lp.detect_lostruns(0.5)
        self.assertTrue(fw_ids)
        time.sleep(4)   # Wait double the expected exec time and test
        fw_ids = self.lp.detect_lostruns(2)
        self.assertTrue(fw_ids)


if __name__ == '__main__':
    unittest.main()
