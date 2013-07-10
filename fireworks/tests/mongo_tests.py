import os
import shutil
import glob
import unittest
from fireworks.core.firework import FireWork, Workflow
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket_launcher import launch_rocket, rapidfire
from fireworks.user_objects.firetasks.script_task import ScriptTask
from fw_tutorials.dynamic_wf.fibadd_task import FibonacciAdderTask
from fw_tutorials.firetask.addition_task import AdditionTask

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Mar 06, 2013'

TESTDB_NAME = 'fireworks_unittest'
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

#TODO: make these tests much better. Right now they are just a crude first line of defense.

# TODO: add dupefinder tests
# TODO: test serialization of YAML on at least one WF

# TODO: cleanup!!

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

    def setUp(self):
        self.old_wd = os.getcwd()

    def test_basic_fw(self):
        test1 = ScriptTask.from_str("python -c 'print \"test1\"'", {'store_stdout': True})
        fw = FireWork(test1)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['stdout'], 'test1\n')

    def test_multi_fw(self):
        test1 = ScriptTask.from_str("python -c 'print \"test1\"'", {'store_stdout': True})
        test2 = ScriptTask.from_str("python -c 'print \"test2\"'", {'store_stdout': True})
        fw = FireWork([test1, test2])
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['stdout'], 'test2\n')

    def test_add_fw(self):
        fw = FireWork(AdditionTask(), {'input_array': [5, 7]})
        self.lp.add_wf(fw)
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['sum'], 12)

    def test_org_wf(self):
        test1 = ScriptTask.from_str("python -c 'print \"test1\"'", {'store_stdout': True})
        test2 = ScriptTask.from_str("python -c 'print \"test2\"'", {'store_stdout': True})
        fw1 = FireWork(test1, fw_id=-1)
        fw2 = FireWork(test2, fw_id=-2)
        wf = Workflow([fw1, fw2], {-1: -2})
        self.lp.add_wf(wf)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['stdout'], 'test1\n')
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(2).action.stored_data['stdout'], 'test2\n')

    def test_fibadder(self):
        fib = FibonacciAdderTask()
        fw = FireWork(fib, {'smaller': 0, 'larger': 1, 'stop_point': 3})
        self.lp.add_wf(fw)
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)

        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['next_fibnum'], 1)
        self.assertEqual(self.lp.get_launch_by_id(2).action.stored_data['next_fibnum'], 2)
        self.assertEqual(self.lp.get_launch_by_id(3).action.stored_data, {})
        self.assertFalse(self.lp.run_exists())

    def tearDown(self):
        self.lp.reset(password=None, require_password=False)
        os.chdir(self.old_wd)
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        for i in glob.glob(os.path.join(MODULE_DIR, 'launcher*')):
            shutil.rmtree(i)

    @classmethod
    def tearDownClass(cls):
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

if __name__ == "__main__":
    unittest.main()