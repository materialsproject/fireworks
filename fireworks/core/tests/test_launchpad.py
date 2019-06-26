# coding: utf-8

from __future__ import unicode_literals, division

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
import filecmp

from pymongo import MongoClient
from pymongo.errors import OperationFailure

from fireworks import Firework, Workflow, LaunchPad, FWorker
from fireworks.core.rocket_launcher import rapidfire, launch_rocket
from fireworks.queue.queue_launcher import setup_offline_job
from fireworks.user_objects.firetasks.script_task import ScriptTask, PyTask
from fireworks.core.tests.tasks import ExceptionTestTask, ExecutionCounterTask, SlowAdditionTask, WaitWFLockTask
from fireworks.core.tests.tasks import DetoursTask
import fireworks.fw_config
from monty.os import cd

TESTDB_NAME = 'fireworks_unittest'
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class AuthenticationTest(unittest.TestCase):
    """Tests whether users are authenticating agains the correct mongo dbs.
    """

    @classmethod
    def setUpClass(cls):
        try:
            client = MongoClient()
            client.not_the_admin_db.command(
                "createUser", "myuser", pwd="mypassword", roles=['dbOwner'])
        except Exception:
            raise unittest.SkipTest(
                'MongoDB is not running in localhost:27017! Skipping tests.')

    def test_no_admin_privileges_for_plebs(self):
        """Normal users can not authenticate against the admin db.
        """
        with self.assertRaises(OperationFailure):
            lp = LaunchPad(name="admin", username="myuser",
                           password="mypassword", authsource="admin")
            lp.db.collection.count()

    def test_authenticating_to_users_db(self):
        """A user should be able to authenticate against a database that they
        are a user of.
        """
        lp = LaunchPad(name="not_the_admin_db", username="myuser",
                       password="mypassword", authsource="not_the_admin_db")
        lp.db.collection.count()

    def test_authsource_infered_from_db_name(self):
        """The default behavior is to authenticate against the db that the user
        is trying to access.
        """
        lp = LaunchPad(name="not_the_admin_db", username="myuser",
                       password="mypassword")
        lp.db.collection.count()


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
        self.lp.reset(password=None, require_password=False,
                      max_reset_wo_password=1000)
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
        fw = Firework(ScriptTask.from_str('echo "hello"'), name="hello")
        wf = Workflow([fw], name='test_workflow')
        self.lp.add_wf(wf)
        self.assertRaises(ValueError, self.lp.reset, '', False, 0)
        self.assertEqual(self.lp.workflows.count(), 1)
        self.lp.reset('',require_password=False)
        self.assertFalse(self.lp.get_fw_ids())
        self.assertFalse(self.lp.get_wf_ids())

        # test failsafe in a strict way
        for _ in range(30):
            self.lp.add_wf(Workflow([Firework(ScriptTask.from_str('echo "hello"'))]))

        self.assertRaises(ValueError, self.lp.reset, '')
        self.lp.reset('', False, 100)  # reset back

    def test_pw_check(self):
        fw = Firework(ScriptTask.from_str('echo "hello"'), name="hello")
        self.lp.add_wf(fw)
        args = ('',)
        self.assertRaises(ValueError,self.lp.reset, *args)

    def test_add_wf(self):
        fw = Firework(ScriptTask.from_str('echo "hello"'), name="hello")
        self.lp.add_wf(fw)
        wf_id = self.lp.get_wf_ids()
        self.assertEqual(len(wf_id), 1)
        for fw_id in self.lp.get_wf_ids():
            wf = self.lp.get_wf_by_fw_id_lzyfw(fw_id)
            self.assertEqual(len(wf.id_fw.keys()), 1)
        fw2 = Firework(ScriptTask.from_str('echo "goodbye"'), name="goodbye")
        wf = Workflow([fw, fw2], name='test_workflow')
        self.lp.add_wf(wf)
        #fw = self.lp.get_fw_ids()
        #self.assertEqual(len(wf.id_fw.keys()), 2)
        fw_ids = self.lp.get_fw_ids()
        self.assertEqual(len(fw_ids), 3)
        self.lp.reset('',require_password=False)

    def test_add_wfs(self):
        ftask = ScriptTask.from_str('echo "lorem ipsum"')
        wfs = []
        for _ in range(50):
            # Add two workflows with 3 and 5 simple fireworks
            wf3 = Workflow([Firework(ftask, name='lorem') for _ in range(3)],
                           name='lorem wf')
            wf5 = Workflow([Firework(ftask, name='lorem') for _ in range(5)],
                           name='lorem wf')
            wfs.extend([wf3, wf5])
        self.lp.bulk_add_wfs(wfs)
        num_fws_total = sum([len(wf.fws) for wf in wfs])
        distinct_fw_ids = self.lp.fireworks.distinct('fw_id', {'name': 'lorem'})
        self.assertEqual(len(distinct_fw_ids), num_fws_total)
        num_wfs_in_db = len(self.lp.get_wf_ids({"name": "lorem wf"}))
        self.assertEqual(num_wfs_in_db, len(wfs))


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
        fw_p = Firework(ScriptTask.from_str(
            'echo "Cronus is the ruler of titans"',
            {'store_stdout':True}), name="parent", fw_id=1)
        # Sibling fireworks
        fw_s1 = Firework(ScriptTask.from_str(
            'echo "Zeus is son of Cronus"',
            {'store_stdout':True}), name="sib1", fw_id=2, parents=fw_p)
        fw_s2 = Firework(ScriptTask.from_str(
            'echo "Poisedon is brother of Zeus"',
            {'store_stdout':True}), name="sib2", fw_id=3, parents=fw_p)
        fw_s3 = Firework(ScriptTask.from_str(
            'echo "Hades is brother of Zeus"',
            {'store_stdout':True}), name="sib3", fw_id=4, parents=fw_p)
        fw_s4 = Firework(ScriptTask.from_str(
            'echo "Demeter is sister & wife of Zeus"',
            {'store_stdout':True}), name="sib4", fw_id=5, parents=fw_p)
        fw_s5 = Firework(ScriptTask.from_str(
            'echo "Lapetus is son of Oceanus"',
            {'store_stdout':True}), name="cousin1", fw_id=6)
        # Children fireworks
        fw_c1 = Firework(ScriptTask.from_str(
            'echo "Ares is son of Zeus"',
            {'store_stdout':True}), name="c1", fw_id=7, parents=fw_s1)
        fw_c2 = Firework(ScriptTask.from_str(
            'echo "Persephone is daughter of Zeus & Demeter and wife of Hades"',
            {'store_stdout':True}), name="c2", fw_id=8, parents=[fw_s1,fw_s4])
        fw_c3 = Firework(ScriptTask.from_str(
            'echo "Makaria is daughter of Hades & Persephone"',
            {'store_stdout':True}), name="c3", fw_id=9, parents=[fw_s3,fw_c2])
        fw_c4 = Firework(ScriptTask.from_str(
            'echo "Dione is descendant of Lapetus"',
            {'store_stdout':True}), name="c4", fw_id=10, parents=fw_s5)
        fw_c5 = Firework(ScriptTask.from_str(
            'echo "Aphrodite is son of of Zeus and Dione"',
            {'store_stdout':True}), name="c5", fw_id=11, parents=[fw_s1,fw_c4])
        fw_c6 = Firework(ScriptTask.from_str(
            'echo "Atlas is son of of Lapetus"',
            {'store_stdout':True}), name="c6", fw_id=12,parents=fw_s5)
        fw_c7 = Firework(ScriptTask.from_str(
            'echo "Maia is daughter of Atlas"',
            {'store_stdout':True}), name="c7", fw_id=13, parents=fw_c6)
        fw_c8 = Firework(ScriptTask.from_str(
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

    @staticmethod
    def _teardown(dests):
        for f in dests:
            if os.path.exists(f):
                os.remove(f)

    def test_pause_fw(self):
        self.lp.pause_fw(self.zeus_fw_id)

        paused_ids = self.lp.get_fw_ids({'state':'PAUSED'})
        self.assertIn(self.zeus_fw_id, paused_ids)
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

            # Setup Zeus to run
            self.lp.resume_fw(self.zeus_fw_id)
            # Launch remaining fireworks
            rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)
            # Check that Zeus and children are all completed now
            completed_ids = set(self.lp.get_fw_ids({'state':'COMPLETED'}))
            self.assertIn(self.zeus_fw_id,completed_ids)
            self.assertTrue(self.zeus_child_fw_ids.issubset(completed_ids))

        except:
            raise


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

    def test_pause_wf(self):
        # pause Workflow containing Zeus
        self.lp.pause_wf(self.zeus_fw_id)
        paused_ids = self.lp.get_fw_ids({'state':'PAUSED'})
        self.assertIn(self.zeus_fw_id,paused_ids)

        # Launch remaining fireworks
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)

        # Check for the state of all fws in Zeus workflow in incomplete fwids
        fws_no_run = set(self.lp.get_fw_ids({'state':{'$nin':['COMPLETED']}}))
        self.assertEqual(fws_no_run,self.all_ids)

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
        print('----------\nafter launch rocket\n--------')

        # defuse Workflow containing Zeus
        print('----------\nstarting defuse rocket\n--------')
        self.lp.defuse_wf(self.zeus_fw_id)
        print('----------\nafter defuse rocket\n--------')
        defused_ids = self.lp.get_fw_ids({'state':'DEFUSED'})
        print('def ids', defused_ids)
        print('zeus id', self.zeus_fw_id)
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
        self.assertEqual(fw.state,'ARCHIVED')

    def test_delete_wf(self):
        # Run a firework before deleting Zeus
        rapidfire(self.lp, self.fworker, nlaunches=1)

        # Get the launch dir
        fw = self.lp.get_fw_by_id(self.lp.get_fw_ids({'state':'COMPLETED'})[0])
        launches = fw.launches
        first_ldir = launches[0].launch_dir
        self.assertTrue(os.path.isdir(first_ldir))

        # Delete workflow containing Zeus.
        self.lp.delete_wf(self.zeus_fw_id)
        # Check if any fireworks and the workflow are available
        with self.assertRaises(ValueError):
            self.lp.get_wf_by_fw_id(self.zeus_fw_id)
        fw_ids = self.lp.get_fw_ids()
        self.assertFalse(fw_ids)
        wf_ids = self.lp.get_wf_ids()
        self.assertFalse(wf_ids)
        # Check that the launch dir has not been deleted
        self.assertTrue(os.path.isdir(first_ldir))

    def test_delete_wf_and_files(self):
        # Run a firework before deleting Zeus
        rapidfire(self.lp, self.fworker, nlaunches=1)

        # Get the launch dir
        fw = self.lp.get_fw_by_id(self.lp.get_fw_ids({'state':'COMPLETED'})[0])
        launches = fw.launches
        first_ldir = launches[0].launch_dir
        self.assertTrue(os.path.isdir(first_ldir))

        # Delete workflow containing Zeus.
        self.lp.delete_wf(self.zeus_fw_id, delete_launch_dirs=True)
        # Check if any fireworks and the workflow are available
        with self.assertRaises(ValueError):
            self.lp.get_wf_by_fw_id(self.zeus_fw_id)
        fw_ids = self.lp.get_fw_ids()
        self.assertFalse(fw_ids)
        wf_ids = self.lp.get_wf_ids()
        self.assertFalse(wf_ids)
        # Check that the launch dir has not been deleted
        self.assertFalse(os.path.isdir(first_ldir))

    def test_rerun_fws2(self):
        # Launch all fireworks
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)
        fw = self.lp.get_fw_by_id(self.zeus_fw_id)
        launches = fw.launches
        first_ldir = launches[0].launch_dir
        ts = datetime.datetime.utcnow()

        # check that all the zeus children are completed
        completed = set(self.lp.get_fw_ids({'state':'COMPLETED'}))
        self.assertTrue(completed.issuperset(set(self.zeus_child_fw_ids)))

        # Rerun Zeus
        self.lp.rerun_fw(self.zeus_fw_id, rerun_duplicates=True)

        # now the children should be waiting
        completed = set(self.lp.get_fw_ids({'state':'WAITING'}))
        self.assertTrue(completed.issuperset(set(self.zeus_child_fw_ids)))

        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)

        fw = self.lp.get_fw_by_id(self.zeus_fw_id)
        launches = fw.launches
        fw_start_t =  launches[0].time_start
        second_ldir = launches[0].launch_dir

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
        fw_timer = Firework(PyTask(func='time.sleep',args=[5]), name="timer")
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

        # Wait for fw to start
        it = 0
        while not any([f.state == 'RUNNING' for f in self.lp.get_wf_by_fw_id_lzyfw(self.fw_id).fws]):
            time.sleep(1)   # Wait 1 sec
            it += 1
            if it == 10:
                raise ValueError("FW never starts running")
        rp.terminate() # Kill the rocket

        l, f, _ = self.lp.detect_lostruns(0.01, max_runtime=5, min_runtime=0)
        self.assertEqual((l, f), ([1], [1]))
        time.sleep(4)   # Wait double the expected exec time and test
        l, f, _ = self.lp.detect_lostruns(2)
        self.assertEqual((l, f), ([1], [1]))

        l, f, _ = self.lp.detect_lostruns(2, min_runtime=10)  # script did not run for 10 secs
        self.assertEqual((l, f), ([], []))

        l, f, _ = self.lp.detect_lostruns(2, max_runtime=-1)  # script ran more than -1 secs
        self.assertEqual((l, f), ([], []))

        l, f, _ = self.lp.detect_lostruns(0.01, max_runtime=5, min_runtime=0, rerun=True)
        self.assertEqual((l, f), ([1], [1]))
        self.assertEqual(self.lp.get_fw_by_id(1).state, 'READY')


    def test_detect_lostruns_defuse(self):
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

        # Wait for fw to start
        it = 0
        while not any([f.state == 'RUNNING' for f in self.lp.get_wf_by_fw_id_lzyfw(self.fw_id).fws]):
            time.sleep(1)   # Wait 1 sec
            it += 1
            if it == 10:
                raise ValueError("FW never starts running")
        rp.terminate() # Kill the rocket

        l, f, i = self.lp.detect_lostruns(0.01)
        self.assertEqual((l, f), ([1], [1]))

        self.lp.defuse_fw(1)

        l, f, i = self.lp.detect_lostruns(0.01, rerun=True)
        self.assertEqual((l, f), ([1], []))
        self.assertEqual(self.lp.get_fw_by_id(1).state, 'DEFUSED')


    def test_state_after_run_start(self):
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

        # Wait for running
        it = 0
        while not any([f.state == 'RUNNING' for f in self.lp.get_wf_by_fw_id_lzyfw(self.fw_id).fws]):
            time.sleep(1)   # Wait 1 sec
            it += 1
            if it == 10:
                raise ValueError("FW never starts running")

        # WF should be running
        wf = self.lp.get_wf_by_fw_id_lzyfw(self.fw_id)
        for fw_id in wf.fw_states:
            self.assertEqual(wf.id_fw[fw_id].state, wf.fw_states[fw_id])
            self.assertEqual(wf.fw_states[fw_id], 'RUNNING')
        rp.terminate()


class WorkflowFireworkStatesTest(unittest.TestCase):
    """
    Class to test the firework states locally cached in workflow.
    The states have to be in sync with the actual firework state.
    """

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
        fw_p = Firework(ScriptTask.from_str(
            'echo "Cronus is the ruler of titans"',
            {'store_stdout':True}), name="parent", fw_id=1)
        # Sibling fireworks
        #fw_s1 = Firework(ScriptTask.from_str(
        #    'echo "Zeus is son of Cronus"',
        #    {'store_stdout':True}), name="sib1", fw_id=2, parents=fw_p)
        # Timed firework
        fw_s1 = Firework(PyTask(func='time.sleep',args=[5]), name="sib1",
                fw_id=2, parents=fw_p)
        fw_s2 = Firework(ScriptTask.from_str(
            'echo "Poisedon is brother of Zeus"',
            {'store_stdout':True}), name="sib2", fw_id=3, parents=fw_p)
        fw_s3 = Firework(ScriptTask.from_str(
            'echo "Hades is brother of Zeus"',
            {'store_stdout':True}), name="sib3", fw_id=4, parents=fw_p)
        fw_s4 = Firework(ScriptTask.from_str(
            'echo "Demeter is sister & wife of Zeus"',
            {'store_stdout':True}), name="sib4", fw_id=5, parents=fw_p)
        fw_s5 = Firework(ScriptTask.from_str(
            'echo "Lapetus is son of Oceanus"',
            {'store_stdout':True}), name="cousin1", fw_id=6)
        # Children fireworks
        fw_c1 = Firework(ScriptTask.from_str(
            'echo "Ares is son of Zeus"',
            {'store_stdout':True}), name="c1", fw_id=7, parents=fw_s1)
        fw_c2 = Firework(ScriptTask.from_str(
            'echo "Persephone is daughter of Zeus & Demeter and wife of Hades"',
            {'store_stdout':True}), name="c2", fw_id=8, parents=[fw_s1,fw_s4])
        fw_c3 = Firework(ScriptTask.from_str(
            'echo "Makaria is daughter of Hades & Persephone"',
            {'store_stdout':True}), name="c3", fw_id=9, parents=[fw_s3,fw_c2])
        fw_c4 = Firework(ScriptTask.from_str(
            'echo "Dione is descendant of Lapetus"',
            {'store_stdout':True}), name="c4", fw_id=10, parents=fw_s5)
        fw_c5 = Firework(ScriptTask.from_str(
            'echo "Aphrodite is son of of Zeus and Dione"',
            {'store_stdout':True}), name="c5", fw_id=11, parents=[fw_s1,fw_c4])
        fw_c6 = Firework(ScriptTask.from_str(
            'echo "Atlas is son of of Lapetus"',
            {'store_stdout':True}), name="c6", fw_id=12,parents=fw_s5)
        fw_c7 = Firework(ScriptTask.from_str(
            'echo "Maia is daughter of Atlas"',
            {'store_stdout':True}), name="c7", fw_id=13, parents=fw_c6)
        fw_c8 = Firework(ScriptTask.from_str(
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

    @staticmethod
    def _teardown(dests):
        for f in dests:
            if os.path.exists(f):
                os.remove(f)

    def test_defuse_fw(self):
        # defuse Zeus
        self.lp.defuse_fw(self.zeus_fw_id)
        # Ensure the states are sync after defusing fw
        wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
        fws = wf.id_fw
        for fw_id in wf.fw_states:
            fw_state = fws[fw_id].state
            fw_cache_state = wf.fw_states[fw_id]
            self.assertEqual(fw_state, fw_cache_state)

        try:
            # Launch remaining fireworks
            rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)
            # Ensure the states are sync after launching remaining fw
            wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
            fws = wf.id_fw
            for fw_id in wf.fw_states:
                fw_state = fws[fw_id].state
                fw_cache_state = wf.fw_states[fw_id]
                self.assertEqual(fw_state, fw_cache_state)
        except:
            raise

    def test_defuse_fw_after_completion(self):
        # Launch rockets in rapidfire
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)
        # defuse Zeus
        self.lp.defuse_fw(self.zeus_fw_id)
        # Ensure the states are sync
        wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
        fws = wf.id_fw
        for fw_id in wf.fw_states:
            fw_state = fws[fw_id].state
            fw_cache_state = wf.fw_states[fw_id]
            self.assertEqual(fw_state, fw_cache_state)

    def test_reignite_fw(self):
        # Defuse Zeus and launch remaining fireworks
        self.lp.defuse_fw(self.zeus_fw_id)
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)

        # Reignite Zeus and his children's fireworks
        self.lp.reignite_fw(self.zeus_fw_id)
        # Ensure the states are sync
        wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
        fws = wf.id_fw
        for fw_id in wf.fw_states:
            fw_state = fws[fw_id].state
            fw_cache_state = wf.fw_states[fw_id]
            self.assertEqual(fw_state, fw_cache_state)

    def test_defuse_wf(self):
        # defuse Workflow containing Zeus
        self.lp.defuse_wf(self.zeus_fw_id)
        defused_ids = self.lp.get_fw_ids({'state':'DEFUSED'})
        self.assertIn(self.zeus_fw_id,defused_ids)

        # Ensure the states are in sync after defusing wf
        wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
        fws = wf.id_fw
        for fw_id in wf.fw_states:
            fw_state = fws[fw_id].state
            fw_cache_state = wf.fw_states[fw_id]
            self.assertEqual(fw_state, fw_cache_state)

    def test_reignite_wf(self):
        # Defuse workflow containing Zeus
        self.lp.defuse_wf(self.zeus_fw_id)

        # Launch any remaining fireworks
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)

        # Reignite Zeus and his children's fireworks and launch them
        self.lp.reignite_wf(self.zeus_fw_id)
        # Ensure the states are sync
        wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
        fws = wf.id_fw
        for fw_id in wf.fw_states:
            fw_state = fws[fw_id].state
            fw_cache_state = wf.fw_states[fw_id]
            self.assertEqual(fw_state, fw_cache_state)

    def test_archive_wf(self):
        # Run a firework before archiving Zeus
        launch_rocket(self.lp, self.fworker)
        # archive Workflow containing Zeus.
        self.lp.archive_wf(self.zeus_fw_id)
        # Ensure the states are sync
        wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
        fws = wf.id_fw
        for fw_id in wf.fw_states:
            fw_state = fws[fw_id].state
            fw_cache_state = wf.fw_states[fw_id]
            self.assertEqual(fw_state, fw_cache_state)

    def test_rerun_fws(self):
        # Launch all fireworks
        rapidfire(self.lp, self.fworker,m_dir=MODULE_DIR)
        fw = self.lp.get_fw_by_id(self.zeus_fw_id)
        launches = fw.launches
        first_ldir = launches[0].launch_dir

        # Rerun Zeus
        self.lp.rerun_fw(self.zeus_fw_id, rerun_duplicates=True)
        # Ensure the states are sync
        wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
        fws = wf.id_fw
        for fw_id in wf.fw_states:
            fw_state = fws[fw_id].state
            fw_cache_state = wf.fw_states[fw_id]
            self.assertEqual(fw_state, fw_cache_state)

    def test_rerun_timed_fws(self):
        # Launch all fireworks in a separate process
        class RapidfireProcess(Process):
            def __init__(self, lpad, fworker):
                super(self.__class__,self).__init__()
                self.lpad = lpad
                self.fworker = fworker

            def run(self):
                rapidfire(self.lpad, self.fworker)
        rp = RapidfireProcess(self.lp, self.fworker)
        rp.start()
        time.sleep(1)   # Wait 1 sec  and kill the running fws
        rp.terminate()
        # Ensure the states are sync
        wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
        fws = wf.id_fw
        for fw_id in wf.fw_states:
            fw_state = fws[fw_id].state
            fw_cache_state = wf.fw_states[fw_id]
            self.assertEqual(fw_state, fw_cache_state)

        # Detect lost runs
        lost_lids, lost_fwids, inconsistent_fwids = self.lp.detect_lostruns(expiration_secs=0.5)
        # Ensure the states are sync
        wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
        fws = wf.id_fw
        for fw_id in wf.fw_states:
            fw_state = fws[fw_id].state
            fw_cache_state = wf.fw_states[fw_id]
            self.assertEqual(fw_state, fw_cache_state)

        # Rerun fizzled runs
        for fw_id in lost_fwids:
            self.lp.rerun_fw(fw_id)
        rp = RapidfireProcess(self.lp, self.fworker)
        rp.start()
        for _ in range(20):
            wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
            fws = wf.id_fw
            if fws[self.zeus_fw_id].state == 'READY':
                time.sleep(0.5)   # Wait 1 sec
            else:
                break
        else:
            # Firework hasn't started yet. Waited too long.
            rp.terminate()
            return

        time.sleep(1)

        # Ensure the states are in sync
        wf = self.lp.get_wf_by_fw_id_lzyfw(self.zeus_fw_id)
        fws = wf.id_fw
        for fw_id in wf.fw_states:
            fw_state = fws[fw_id].state
            fw_cache_state = wf.fw_states[fw_id]
            self.assertEqual(fw_state, fw_cache_state)
        rp.terminate()


class LaunchPadRerunExceptionTest(unittest.TestCase):

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
        fireworks.core.firework.EXCEPT_DETAILS_ON_RERUN = True

        self.error_test_dict = {'error': 'description', 'error_code': 1}
        fw = Firework([ExecutionCounterTask(),
                       ScriptTask.from_str('date +"%s %N"', parameters={'stdout_file': 'date_file'}),
                      ExceptionTestTask(exc_details=self.error_test_dict)])
        self.lp.add_wf(fw)
        ExecutionCounterTask.exec_counter = 0
        ExceptionTestTask.exec_counter = 0

        self.old_wd = os.getcwd()

    def tearDown(self):
        self.lp.reset(password=None, require_password=False)
        # Delete launch locations
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        os.chdir(self.old_wd)
        for ldir in glob.glob(os.path.join(MODULE_DIR, "launcher_*")):
            shutil.rmtree(ldir)

    def test_except_details_on_rerun(self):
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)
        self.assertEqual(os.getcwd(), MODULE_DIR)
        self.lp.rerun_fw(1)
        fw = self.lp.get_fw_by_id(1)
        self.assertEqual(fw.spec['_exception_details'], self.error_test_dict)

    def test_task_level_rerun(self):
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)
        self.assertEqual(os.getcwd(), MODULE_DIR)
        self.lp.rerun_fw(1, recover_launch='last')
        self.lp.update_spec([1], {'skip_exception': True})
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)
        self.assertEqual(os.getcwd(), MODULE_DIR)
        dirs = sorted(glob.glob(os.path.join(MODULE_DIR, "launcher_*")))
        self.assertEqual(self.lp.get_fw_by_id(1).state, 'COMPLETED')
        self.assertEqual(ExecutionCounterTask.exec_counter, 1)
        self.assertEqual(ExceptionTestTask.exec_counter, 2)
        self.assertFalse(os.path.exists(os.path.join(dirs[1], "date_file")))
        # Ensure rerun deletes recovery by default
        self.lp.rerun_fw(1)
        fw = self.lp.get_fw_by_id(1)
        self.assertFalse("_recovery" in fw.spec)

    def test_task_level_rerun_cp(self):
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)
        self.assertEqual(os.getcwd(), MODULE_DIR)
        self.lp.rerun_fw(1, recover_launch='last', recover_mode="cp")
        self.lp.update_spec([1], {'skip_exception': True})
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)
        self.assertEqual(os.getcwd(), MODULE_DIR)
        dirs = sorted(glob.glob(os.path.join(MODULE_DIR, "launcher_*")))
        self.assertEqual(self.lp.get_fw_by_id(1).state, 'COMPLETED')
        self.assertEqual(ExecutionCounterTask.exec_counter, 1)
        self.assertEqual(ExceptionTestTask.exec_counter, 2)
        self.assertTrue(filecmp.cmp(os.path.join(dirs[0], "date_file"), os.path.join(dirs[1], "date_file")))

    def test_task_level_rerun_prev_dir(self):
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)
        self.assertEqual(os.getcwd(), MODULE_DIR)
        self.lp.rerun_fw(1, recover_launch='last', recover_mode="prev_dir")
        self.lp.update_spec([1], {'skip_exception': True})
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)
        fw = self.lp.get_fw_by_id(1)
        self.assertEqual(os.getcwd(), MODULE_DIR)
        self.assertEqual(fw.state, 'COMPLETED')
        self.assertEqual(fw.launches[0].launch_dir, fw.archived_launches[0].launch_dir)
        self.assertEqual(ExecutionCounterTask.exec_counter, 1)
        self.assertEqual(ExceptionTestTask.exec_counter, 2)


class WFLockTest(unittest.TestCase):

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
        # set the defaults in the init of wflock to break the lock quickly
        fireworks.core.launchpad.WFLock(3, False).__init__.__func__.__defaults__= (3, False)

        self.error_test_dict = {'error': 'description', 'error_code': 1}
        fw_slow = Firework(SlowAdditionTask(), spec={'seconds': 10}, fw_id=1)
        fw_fast = Firework(WaitWFLockTask(), fw_id=2, spec={'_add_launchpad_and_fw_id': True})
        fw_child = Firework(ScriptTask.from_str('echo "child"'), fw_id=3)
        wf = Workflow([fw_slow, fw_fast, fw_child], {fw_slow: fw_child, fw_fast: fw_child})
        self.lp.add_wf(wf)

        self.old_wd = os.getcwd()

    def tearDown(self):
        self.lp.reset(password=None, require_password=False)
        # Delete launch locations
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        os.chdir(self.old_wd)
        for ldir in glob.glob(os.path.join(MODULE_DIR, "launcher_*")):
            shutil.rmtree(ldir)

    def test_fix_db_inconsistencies_completed(self):
        class RocketProcess(Process):
            def __init__(self, lpad, fworker, fw_id):
                super(self.__class__,self).__init__()
                self.lpad = lpad
                self.fworker = fworker
                self.fw_id = fw_id

            def run(self):
                launch_rocket(self.lpad, self.fworker, fw_id=self.fw_id)
        # Launch the slow firework in a separate process
        rp = RocketProcess(self.lp, self.fworker, fw_id=1)
        rp.start()

        time.sleep(1)
        launch_rocket(self.lp, self.fworker, fw_id=2)

        # wait for the slow to complete
        rp.join()

        fast_fw = self.lp.get_fw_by_id(2)

        if fast_fw.state == 'FIZZLED':
            stacktrace = self.lp.launches.find_one(
                {'fw_id': 2}, {'action.stored_data._exception._stacktrace': 1})['action']['stored_data']['_exception']['_stacktrace']
            if 'SkipTest' in stacktrace:
                self.skipTest("The test didn't run correctly")

        self.assertEqual(fast_fw.state, 'RUNNING')

        child_fw = self.lp.get_fw_by_id(3)

        self.assertTrue("SlowAdditionTask" in child_fw.spec)
        self.assertFalse("WaitWFLockTask" in child_fw.spec)



        self.lp._refresh_wf(fw_id=2)

        child_fw = self.lp.get_fw_by_id(3)

        self.assertTrue("WaitWFLockTask" in child_fw.spec)

        fast_fw = self.lp.get_fw_by_id(2)

        self.assertEqual(fast_fw.state, 'COMPLETED')

    def test_fix_db_inconsistencies_fizzled(self):

        class RocketProcess(Process):
            def __init__(self, lpad, fworker, fw_id):
                super(self.__class__,self).__init__()
                self.lpad = lpad
                self.fworker = fworker
                self.fw_id = fw_id

            def run(self):
                launch_rocket(self.lpad, self.fworker, fw_id=self.fw_id)

        self.lp.update_spec([2], {'fizzle': True})

        # Launch the slow firework in a separate process
        rp = RocketProcess(self.lp, self.fworker, fw_id=1)
        rp.start()

        time.sleep(1)
        launch_rocket(self.lp, self.fworker, fw_id=2)

        # wait for the slow to complete
        rp.join()

        fast_fw = self.lp.get_fw_by_id(2)

        if fast_fw.state == 'FIZZLED':
            stacktrace = self.lp.launches.find_one(
                {'fw_id': 2}, {'action.stored_data._exception._stacktrace': 1})['action']['stored_data']['_exception']['_stacktrace']
            if 'SkipTest' in stacktrace:
                self.skipTest("The test didn't run correctly")

        self.assertEqual(fast_fw.state, 'RUNNING')

        child_fw = self.lp.get_fw_by_id(3)

        self.assertTrue("SlowAdditionTask" in child_fw.spec)
        self.assertFalse("WaitWFLockTask" in child_fw.spec)

        self.lp._refresh_wf(fw_id=2)

        fast_fw = self.lp.get_fw_by_id(2)

        self.assertEqual(fast_fw.state, 'FIZZLED')


class LaunchPadOfflineTest(unittest.TestCase):

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
        fireworks.core.firework.EXCEPT_DETAILS_ON_RERUN = True

        self.error_test_dict = {'error': 'description', 'error_code': 1}
        fw = Firework(ScriptTask.from_str(
            'echo "test offline"',
            {'store_stdout':True}), name="offline_fw", fw_id=1)
        self.lp.add_wf(fw)

        self.launch_dir = os.path.join(MODULE_DIR, "launcher_offline")
        os.makedirs(self.launch_dir)

        self.old_wd = os.getcwd()

    def tearDown(self):
        self.lp.reset(password=None, require_password=False)
        # Delete launch locations
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        os.chdir(self.old_wd)
        for ldir in glob.glob(os.path.join(MODULE_DIR, "launcher_*")):
            shutil.rmtree(ldir, ignore_errors=True)

    def test__recover_completed(self):
        fw, launch_id = self.lp.reserve_fw(self.fworker, self.launch_dir)
        fw = self.lp.get_fw_by_id(1)
        with cd(self.launch_dir):
            setup_offline_job(self.lp, fw, launch_id)

            # launch rocket without launchpad to trigger offline mode
            launch_rocket(launchpad=None, fworker=self.fworker, fw_id=1)

        self.assertIsNone(self.lp.recover_offline(launch_id))

        fw = self.lp.get_fw_by_id(launch_id)

        self.assertEqual(fw.state, 'COMPLETED')


    def test_recover_errors(self):
        fw, launch_id = self.lp.reserve_fw(self.fworker, self.launch_dir)
        fw = self.lp.get_fw_by_id(1)
        with cd(self.launch_dir):
            setup_offline_job(self.lp, fw, launch_id)

        # remove the directory to cause an exception
        shutil.rmtree(self.launch_dir)

        # recover ignoring errors
        self.assertIsNotNone(self.lp.recover_offline(launch_id, ignore_errors=True, print_errors=True))

        fw = self.lp.get_fw_by_id(launch_id)

        self.assertEqual(fw.state, 'RESERVED')

        #fizzle
        self.assertIsNotNone(self.lp.recover_offline(launch_id, ignore_errors=False))

        fw = self.lp.get_fw_by_id(launch_id)

        self.assertEqual(fw.state, 'FIZZLED')


class GridfsStoredDataTest(unittest.TestCase):
    """
    Tests concerning the storage of data in Gridfs when the size of the
    documents exceed the 16MB limit.
    """

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

    def tearDown(self):
        self.lp.reset(password=None,require_password=False)
        # Delete launch locations
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        os.chdir(self.old_wd)
        for ldir in glob.glob(os.path.join(MODULE_DIR,"launcher_*")):
            shutil.rmtree(ldir)

    def test_many_detours(self):
        task = DetoursTask(n_detours=2000, data_per_detour=["a" * 100] * 100)
        fw = Firework([task])
        self.lp.add_wf(fw)

        rapidfire(self.lp, self.fworker, nlaunches=1)

        fw = self.lp.get_fw_by_id(1)

        self.assertEqual(fw.state, 'COMPLETED')

        launch_db = self.lp.launches.find_one({"launch_id":1})
        self.assertIsNotNone(launch_db["action"]["gridfs_id"])
        self.assertNotIn("detours", launch_db["action"])

        self.assertEqual(self.lp.get_fw_ids(count_only=True), 2001)

        launch_full = self.lp.get_launch_by_id(1)
        self.assertEqual(len(launch_full.action.detours), 2000)

        wf = self.lp.get_wf_by_fw_id_lzyfw(1)
        self.assertEqual(len(wf.id_fw[1].launches[0].action.detours), 2000)

    def test_many_detours_offline(self):
        task = DetoursTask(n_detours=2000, data_per_detour=["a" * 100] * 100)
        fw = Firework([task])
        self.lp.add_wf(fw)

        launch_dir = os.path.join(MODULE_DIR, "launcher_offline")
        os.makedirs(launch_dir)
        fw, launch_id = self.lp.reserve_fw(self.fworker, launch_dir)
        fw = self.lp.get_fw_by_id(1)
        with cd(launch_dir):
            setup_offline_job(self.lp, fw, launch_id)

            # launch rocket without launchpad to trigger offline mode
            launch_rocket(launchpad=None, fworker=self.fworker, fw_id=1)

        self.assertIsNone(self.lp.recover_offline(launch_id))

        launch_db = self.lp.launches.find_one({"launch_id": launch_id})
        self.assertIsNotNone(launch_db["action"]["gridfs_id"])
        self.assertNotIn("detours", launch_db["action"])

        launch_full = self.lp.get_launch_by_id(1)
        self.assertEqual(len(launch_full.action.detours), 2000)


if __name__ == '__main__':
    unittest.main()
