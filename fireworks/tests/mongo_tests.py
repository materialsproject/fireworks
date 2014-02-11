import os
import shutil
import glob
import unittest
from fireworks.core.firework import FireWork, Workflow
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket_launcher import launch_rocket, rapidfire
from fireworks.features.background_task import BackgroundTask
from fireworks.user_objects.firetasks.fileio_tasks import FileTransferTask, FileWriteTask
from fireworks.user_objects.firetasks.script_task import ScriptTask
from fireworks.user_objects.firetasks.templatewriter_task import TemplateWriterTask
from fw_tutorials.dynamic_wf.fibadd_task import FibonacciAdderTask
from fw_tutorials.firetask.addition_task import AdditionTask
import six

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
            'stdout'], str(six.b('test1\n')))

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
            str(six.b("test2\n")))

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
                         str(six.b('test1\n')))
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(2).action.stored_data['stdout'],
                         str(six.b('test2\n')))

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