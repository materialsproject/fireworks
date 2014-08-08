from multiprocessing import Pool
import os
import random
import shutil
import glob
import unittest
import time
from fireworks.core.firework import FireWork, Workflow
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad, WFLock
from fireworks.core.rocket_launcher import launch_rocket, rapidfire
from fireworks.features.background_task import BackgroundTask
from fireworks.fw_config import WFLOCK_EXPIRATION_KILL
from fireworks.user_objects.dupefinders.dupefinder_exact import DupeFinderExact
from fireworks.user_objects.firetasks.fileio_tasks import FileTransferTask, FileWriteTask
from fireworks.user_objects.firetasks.script_task import ScriptTask, PyTask
from fireworks.user_objects.firetasks.templatewriter_task import TemplateWriterTask
from fw_tutorials.dynamic_wf.fibadd_task import FibonacciAdderTask
from fw_tutorials.firetask.addition_task import AdditionTask
from fireworks.tests.tasks import DummyTask
import six

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Mar 06, 2013'

TESTDB_NAME = 'fireworks_unittest'
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
NCORES_PARALLEL_TEST = 4

#TODO: make these tests much better. Right now they are just a crude first line of defense.

# TODO: add dupefinder tests
# TODO: test serialization of YAML on at least one WF

# TODO: cleanup!!

def random_launch(lp_creds):
        lp = LaunchPad.from_dict(lp_creds)
        while lp.run_exists(None):
            launch_rocket(lp)
            time.sleep(random.random()/3+0.1)

def throw_error(msg):
    raise ValueError(msg)

class MongoTests(unittest.TestCase):

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

    def _teardown(self, dests):
        for f in dests:
            if os.path.exists(f):
                os.remove(f)

    def setUp(self):
        self.old_wd = os.getcwd()

    def test_basic_fw(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'",
                                    {'store_stdout': True})
        fw = FireWork(test1)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data[
            'stdout'], 'test1\n')

    def test_multi_fw(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'",
                                    {'store_stdout': True})
        test2 = ScriptTask.from_str("python -c 'print(\"test2\")'",
                                    {'store_stdout': True})
        fw = FireWork([test1, test2])
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(
            self.lp.get_launch_by_id(1).action.stored_data['stdout'],
            "test2\n")

    def test_multi_fw_complex(self):

        dest1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inputs.txt')
        dest2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_file.txt')
        self._teardown([dest1, dest2])
        try:
            # create the FireWork consisting of multiple tasks
            firetask1 = TemplateWriterTask({'context': {'opt1': 5.0, 'opt2': 'fast method'}, 'template_file': 'simple_template.txt', 'output_file': dest1})
            firetask2 = FileTransferTask({'files': [{'src': dest1, 'dest': dest2}], 'mode': 'copy'})
            fw = FireWork([firetask1, firetask2])

            # store workflow and launch it locally, single shot
            self.lp.add_wf(fw)
            launch_rocket(self.lp, FWorker())

            # read inputs.txt, words.txt, dest
            for d in [dest1, dest2]:
                with open(d) as f:
                    self.assertEqual(f.read(), 'option1 = 5.0\noption2 = fast method')

        finally:
            self._teardown([dest1, dest2])


    def test_backgroundtask(self):
        dest1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hello.txt')
        self._teardown([dest1])

        try:
            test1 = ScriptTask.from_str("python -c 'print(\"testing background...\")'",
                                        {'store_stdout': True})

            bg_task1 = BackgroundTask(FileWriteTask({'files_to_write': [{'filename': dest1, 'contents': 'hello'}]}), num_launches=1, run_on_finish=True)
            fw = FireWork(test1, spec={'_background_tasks': [bg_task1]})
            self.lp.add_wf(fw)
            launch_rocket(self.lp, self.fworker)

            with open(dest1) as f:
                    self.assertEqual(f.read(), 'hello')

        finally:
            self._teardown([dest1])

    def test_add_fw(self):
        fw = FireWork(AdditionTask(), {'input_array': [5, 7]})
        self.lp.add_wf(fw)
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['sum'], 12)

    def test_org_wf(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'",
                                    {'store_stdout': True})
        test2 = ScriptTask.from_str("python -c 'print(\"test2\")'",
                                    {'store_stdout': True})
        fw1 = FireWork(test1, fw_id=-1)
        fw2 = FireWork(test2, fw_id=-2)
        wf = Workflow([fw1, fw2], {-1: -2})
        self.lp.add_wf(wf)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['stdout'],
                         'test1\n')
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(2).action.stored_data['stdout'],
                         'test2\n')

    def test_fibadder(self):
        fib = FibonacciAdderTask()
        fw = FireWork(fib, {'smaller': 0, 'larger': 1, 'stop_point': 3})
        self.lp.add_wf(fw)
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)

        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['next_fibnum'], 1)
        self.assertEqual(self.lp.get_launch_by_id(2).action.stored_data['next_fibnum'], 2)
        self.assertEqual(self.lp.get_launch_by_id(3).action.stored_data, {})
        self.assertFalse(self.lp.run_exists())

    def test_parallel_fibadder(self):
        # this is really testing to see if a Workflow can handle multiple FWs updating it at once
        parent = FireWork(ScriptTask.from_str("python -c 'print(\"test1\")'", {'store_stdout': True}), fw_id=1)
        fib1 = FireWork(FibonacciAdderTask(), {'smaller': 0, 'larger': 1, 'stop_point': 30}, fw_id=2)
        fib2 = FireWork(FibonacciAdderTask(), {'smaller': 0, 'larger': 1, 'stop_point': 30}, fw_id=3)
        wf = Workflow([parent, fib1, fib2], {1: [2, 3]})
        self.lp.add_wf(wf)

        p = Pool(NCORES_PARALLEL_TEST)

        creds_array = [self.lp.to_dict()] * NCORES_PARALLEL_TEST
        p.map(random_launch, creds_array)


    def test_fworkerenv(self):
        t = DummyTask()
        fw = FireWork(t)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data[
                             'data'],
                         "hello")
        self.lp.add_wf(fw)
        launch_rocket(self.lp, FWorker(env={"hello": "world"}))
        self.assertEqual(self.lp.get_launch_by_id(2).action.stored_data[
                             'data'],
                         "world")

    def test_spec_copy(self):
        task1 = ScriptTask.from_str('echo "Task 1"')
        task2 = ScriptTask.from_str('echo "Task 2"')

        spec = {'_category': 'dummy_category'}

        fw1 = FireWork(task1, fw_id=1, name='Task 1', spec=spec)
        fw2 = FireWork(task2, fw_id=2, name='Task 2', spec=spec)

        self.lp.add_wf(Workflow([fw1, fw2]))

        self.assertEqual(self.lp.get_fw_by_id(1).tasks[0]['script'][0], 'echo "Task 1"')
        self.assertEqual(self.lp.get_fw_by_id(2).tasks[0]['script'][0], 'echo "Task 2"')

    def test_delete_fw(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {'store_stdout': True})
        fw = FireWork(test1)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data[
            'stdout'], 'test1\n')
        self.lp.delete_wf(fw.fw_id)
        self.assertRaises(ValueError, self.lp.get_fw_by_id, fw.fw_id)
        self.assertRaises(ValueError, self.lp.get_launch_by_id, 1)


    def test_duplicate_delete_fw(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {'store_stdout': True})
        fw = FireWork(test1, {"_dupefinder": DupeFinderExact()})
        self.lp.add_wf(fw)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        launch_rocket(self.lp, self.fworker)

        self.lp.delete_wf(2)
        self.assertRaises(ValueError, self.lp.get_fw_by_id, 2)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data[
            'stdout'], 'test1\n')

    def test_dupefinder(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {'store_stdout': True})
        fw = FireWork(test1, {"_dupefinder": DupeFinderExact()})
        self.lp.add_wf(fw)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        launch_rocket(self.lp, self.fworker)

        self.assertEqual(self.lp.launches.count(), 1)

    def test_force_lock_removal(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {'store_stdout': True})
        fw = FireWork(test1, {"_dupefinder": DupeFinderExact()}, fw_id=1)
        self.lp.add_wf(fw)
        self.assertEqual(WFLOCK_EXPIRATION_KILL, True)
        # add a manual lock
        with WFLock(self.lp, 1):
            with WFLock(self.lp, 1, expire_secs=1):
                self.assertTrue(True)  # dummy to make sure we got here

    def test_fizzle(self):
        p = PyTask(func="fireworks.tests.mongo_tests.throw_error", args=["Testing; this error is normal."])
        fw = FireWork(p)
        self.lp.add_wf(fw)
        self.assertTrue(launch_rocket(self.lp, self.fworker))
        self.assertEqual(self.lp.get_fw_by_id(1).state, 'FIZZLED')
        self.assertFalse(launch_rocket(self.lp, self.fworker))

    def test_defuse(self):
        p = PyTask(func="fireworks.tests.mongo_tests.throw_error", args=["This should not happen"])
        fw = FireWork(p)
        self.lp.add_wf(fw)
        self.lp.defuse_fw(fw.fw_id)
        self.assertFalse(launch_rocket(self.lp, self.fworker))

    def test_archive(self):
        p = PyTask(func="fireworks.tests.mongo_tests.throw_error", args=["This should not happen"])
        fw = FireWork(p)
        self.lp.add_wf(fw)
        self.lp.archive_wf(fw.fw_id)
        self.assertFalse(launch_rocket(self.lp, self.fworker))

    def tearDown(self):
        self.lp.reset(password=None, require_password=False)
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        os.chdir(self.old_wd)
        for i in glob.glob(os.path.join(MODULE_DIR, 'launcher*')):
            shutil.rmtree(i)

    @classmethod
    def tearDownClass(cls):
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

if __name__ == "__main__":
    unittest.main()