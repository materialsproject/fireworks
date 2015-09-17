# coding: utf-8

from __future__ import unicode_literals
import json

from multiprocessing import Pool
import os
import random
import shutil
import glob
import unittest
import time
from fireworks import explicit_serialize, FWAction
from fireworks.core.firework import Firework, Workflow, FireTaskBase
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad, WFLock
from fireworks.core.rocket_launcher import launch_rocket, rapidfire
from fireworks.features.background_task import BackgroundTask
from fireworks.fw_config import WFLOCK_EXPIRATION_KILL
from fireworks.queue.queue_launcher import setup_offline_job
from fireworks.user_objects.dupefinders.dupefinder_exact import DupeFinderExact
from fireworks.user_objects.firetasks.fileio_tasks import FileTransferTask, FileWriteTask
from fireworks.user_objects.firetasks.script_task import ScriptTask, PyTask
from fireworks.user_objects.firetasks.templatewriter_task import TemplateWriterTask
from fw_tutorials.dynamic_wf.fibadd_task import FibonacciAdderTask
from fw_tutorials.firetask.addition_task import AdditionTask
from fireworks.tests.tasks import DummyFWEnvTask, DummyJobPassTask, DummyLPTask
from fireworks.features.stats import FWStats
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

def random_launch(lp_creds):
        lp = LaunchPad.from_dict(lp_creds)
        while lp.run_exists(None):
            launch_rocket(lp)
            time.sleep(random.random()/3+0.1)

def throw_error(msg):
    raise ValueError(msg)

@explicit_serialize
class MultipleDetourTask(FireTaskBase):

    def run_task(self, fw_spec):
        print('Running the Multiple Detour Task')
        dt1 = Firework(ScriptTask.from_str('echo "this is intermediate job 1"'))
        dt2 = Firework(ScriptTask.from_str('echo "this is intermediate job 2"'))
        dt3 = Firework(ScriptTask.from_str('echo "this is intermediate job 3"'))
        return FWAction(detours=[dt1, dt2, dt3])

@explicit_serialize
class UpdateSpecTask(FireTaskBase):
    def run_task(self, fw_spec):
        print('Running the Update Spec Task')
        dt1 = Firework(ScriptTask.from_str('echo "this is dummy job 1"'))
        return FWAction(update_spec={"dummy1": 1}, additions=[dt1])

@explicit_serialize
class ModSpecTask(FireTaskBase):
    def run_task(self, fw_spec):
        print('Running the Mod Spec Task')
        return FWAction(mod_spec=[{"_push": {"dummy2": True}}])


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
        self.lp.reset(password=None, require_password=False)
        self.old_wd = os.getcwd()

    def tearDown(self):
        self.lp.reset(password=None, require_password=False)
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        if os.path.exists(os.path.join('FW_offline.json')):
            os.remove('FW_offline.json')
        if os.path.exists(os.path.join('FW_ping.json')):
            os.remove('FW_ping.json')
        os.chdir(self.old_wd)
        for i in glob.glob(os.path.join(MODULE_DIR, 'launcher*')):
            shutil.rmtree(i)

    def test_basic_fw(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'",
                                    {'store_stdout': True})
        fw = Firework(test1)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data[
            'stdout'], 'test1\n')

    def test_basic_fw_offline(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'",
                                    {'store_stdout': True})
        fw = Firework(test1)
        self.lp.add_wf(fw)

        fw, launch_id = self.lp.reserve_fw(FWorker(), os.getcwd())

        setup_offline_job(self.lp, fw, launch_id)

        launch_rocket(None, self.fworker)

        with open(os.path.join(os.getcwd(), "FW_offline.json")) as f:
            fwo = json.load(f)
            self.assertEquals(fwo["state"], "COMPLETED")
            self.assertEquals(fwo["launch_id"], 1)
            self.assertEquals(fwo["fwaction"], {'update_spec': {}, 'mod_spec': [], 'stored_data': {'returncode': 0, 'stdout': u'test1\n', 'all_returncodes': [0]}, 'exit': False, 'detours': [], 'additions': [], 'defuse_children': False})

        with open(os.path.join(os.getcwd(), "FW_ping.json")) as f:
            fwp = json.load(f)
            self.assertIsNotNone(fwp["ping_time"])

        l = self.lp.offline_runs.find_one({"completed": False, "deprecated": False}, {"launch_id": 1})
        self.lp.recover_offline(l['launch_id'])
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['stdout'], 'test1\n')

    def test_multi_fw(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'",
                                    {'store_stdout': True})
        test2 = ScriptTask.from_str("python -c 'print(\"test2\")'",
                                    {'store_stdout': True})
        fw = Firework([test1, test2])
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
            # create the Firework consisting of multiple tasks
            firetask1 = TemplateWriterTask({'context': {'opt1': 5.0, 'opt2': 'fast method'}, 'template_file': 'simple_template.txt', 'output_file': dest1})
            firetask2 = FileTransferTask({'files': [{'src': dest1, 'dest': dest2}], 'mode': 'copy'})
            fw = Firework([firetask1, firetask2])

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
            fw = Firework(test1, spec={'_background_tasks': [bg_task1]})
            self.lp.add_wf(fw)
            launch_rocket(self.lp, self.fworker)

            with open(dest1) as f:
                    self.assertEqual(f.read(), 'hello')

        finally:
            self._teardown([dest1])

    def test_add_fw(self):
        fw = Firework(AdditionTask(), {'input_array': [5, 7]})
        self.lp.add_wf(fw)
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['sum'], 12)

    def test_org_wf(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'",
                                    {'store_stdout': True})
        test2 = ScriptTask.from_str("python -c 'print(\"test2\")'",
                                    {'store_stdout': True})
        fw1 = Firework(test1, fw_id=-1)
        fw2 = Firework(test2, fw_id=-2)
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
        fw = Firework(fib, {'smaller': 0, 'larger': 1, 'stop_point': 3})
        self.lp.add_wf(fw)
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)

        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['next_fibnum'], 1)
        self.assertEqual(self.lp.get_launch_by_id(2).action.stored_data['next_fibnum'], 2)
        self.assertEqual(self.lp.get_launch_by_id(3).action.stored_data, {})
        self.assertFalse(self.lp.run_exists())

    def test_parallel_fibadder(self):
        # this is really testing to see if a Workflow can handle multiple FWs updating it at once
        parent = Firework(ScriptTask.from_str("python -c 'print(\"test1\")'", {'store_stdout': True}))
        fib1 = Firework(FibonacciAdderTask(), {'smaller': 0, 'larger': 1, 'stop_point': 30}, parents=[parent])
        fib2 = Firework(FibonacciAdderTask(), {'smaller': 0, 'larger': 1, 'stop_point': 30}, parents=[parent])
        fib3 = Firework(FibonacciAdderTask(), {'smaller': 0, 'larger': 1, 'stop_point': 30}, parents=[parent])
        fib4 = Firework(FibonacciAdderTask(), {'smaller': 0, 'larger': 1, 'stop_point': 30}, parents=[parent])
        wf = Workflow([parent, fib1, fib2, fib3, fib4])
        self.lp.add_wf(wf)

        p = Pool(NCORES_PARALLEL_TEST)

        creds_array = [self.lp.to_dict()] * NCORES_PARALLEL_TEST
        p.map(random_launch, creds_array)

    def test_multi_detour(self):
        fw1 = Firework([MultipleDetourTask()], fw_id=1)
        fw2 = Firework([ScriptTask.from_str('echo "DONE"')], parents=[fw1], fw_id=2)
        self.lp.add_wf(Workflow([fw1, fw2]))
        rapidfire(self.lp)
        links = self.lp.get_wf_by_fw_id(1).links
        self.assertEqual(set(links[1]), set([2, 3, 4, 5]))
        self.assertEqual(set(links[2]), set([]))
        self.assertEqual(set(links[3]), set([2]))
        self.assertEqual(set(links[4]), set([2]))
        self.assertEqual(set(links[5]), set([2]))

    def test_fw_env(self):
        t = DummyFWEnvTask()
        fw = Firework(t)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['data'], "hello")
        self.lp.add_wf(fw)
        launch_rocket(self.lp, FWorker(env={"hello": "world"}))
        self.assertEqual(self.lp.get_launch_by_id(2).action.stored_data[
                             'data'],
                         "world")

    def test_job_info(self):
        fw1 = Firework([ScriptTask.from_str('echo "Testing job info"')], spec={"_pass_job_info": True}, fw_id=1)
        fw2 = Firework([DummyJobPassTask()], parents=[fw1], spec={"_pass_job_info": True, "target": 1}, fw_id=2)
        fw3 = Firework([DummyJobPassTask()], parents=[fw2], spec={"target":2}, fw_id=3)
        self.lp.add_wf(Workflow([fw1, fw2, fw3]))
        launch_rocket(self.lp, self.fworker)

        target_fw_id = self.lp.get_fw_ids({"spec.target": 1})[0]
        modified_spec = self.lp.get_fw_by_id(target_fw_id).spec
        """
        cnt = 0
        while '_job_info' not in modified_spec and cnt < 5:
            print(modified_spec)
            modified_spec = self.lp.get_fw_by_id(target_fw_id).spec
            time.sleep(5)
            cnt += 1
        """

        self.assertIsNotNone(modified_spec['_job_info'])
        self.assertIsNotNone(modified_spec['_job_info'][0]["launch_dir"])
        self.assertEqual(modified_spec['_job_info'][0]['name'], 'Unnamed FW')
        self.assertEqual(modified_spec['_job_info'][0]['fw_id'], 1)

        launch_rocket(self.lp, self.fworker)

        target_fw_id = self.lp.get_fw_ids({"spec.target": 2})[0]
        modified_spec = self.lp.get_fw_by_id(target_fw_id).spec

        """
        cnt = 0
        while '_job_info' not in modified_spec and cnt < 5:
            print(modified_spec)
            modified_spec = self.lp.get_fw_by_id(target_fw_id).spec
            time.sleep(5)
            cnt += 1
        """

        self.assertEqual(len(modified_spec['_job_info']), 2)

    def test_preserve_fworker(self):
        fw1 = Firework([ScriptTask.from_str('echo "Testing preserve FWorker"')], spec={"_preserve_fworker": True}, fw_id=1)
        fw2 = Firework([ScriptTask.from_str('echo "Testing preserve FWorker pt 2"')], spec={"target": 1}, parents=[fw1], fw_id=2)
        self.lp.add_wf(Workflow([fw1, fw2]))
        launch_rocket(self.lp, self.fworker)

        target_fw_id = self.lp.get_fw_ids({"spec.target": 1})[0]

        modified_spec = self.lp.get_fw_by_id(target_fw_id).spec

        """
        cnt = 0
        while '_fworker' not in modified_spec and cnt < 5:
            modified_spec = self.lp.get_fw_by_id(target_fw_id).spec
            print(modified_spec)
            time.sleep(5)
            cnt += 1
        """

        self.assertIsNotNone(modified_spec['_fworker'])

    def test_add_lp_and_fw_id(self):
        fw1 = Firework([DummyLPTask()], spec={"_add_launchpad_and_fw_id": True})
        self.lp.add_wf(fw1)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data['fw_id'], 1)
        self.assertIsNotNone(self.lp.get_launch_by_id(1).action.stored_data['host'])

    def test_spec_copy(self):
        task1 = ScriptTask.from_str('echo "Task 1"')
        task2 = ScriptTask.from_str('echo "Task 2"')

        spec = {'_category': 'dummy_category'}

        fw1 = Firework(task1, fw_id=1, name='Task 1', spec=spec)
        fw2 = Firework(task2, fw_id=2, name='Task 2', spec=spec)

        self.lp.add_wf(Workflow([fw1, fw2]))

        self.assertEqual(self.lp.get_fw_by_id(1).tasks[0]['script'][0], 'echo "Task 1"')
        self.assertEqual(self.lp.get_fw_by_id(2).tasks[0]['script'][0], 'echo "Task 2"')

    def test_delete_fw(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {'store_stdout': True})
        fw = Firework(test1)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.get_launch_by_id(1).action.stored_data[
            'stdout'], 'test1\n')
        self.lp.delete_wf(fw.fw_id)
        self.assertRaises(ValueError, self.lp.get_fw_by_id, fw.fw_id)
        self.assertRaises(ValueError, self.lp.get_launch_by_id, 1)


    def test_duplicate_delete_fw(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {'store_stdout': True})
        fw = Firework(test1, {"_dupefinder": DupeFinderExact()})
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
        fw = Firework(test1, {"_dupefinder": DupeFinderExact()})
        self.lp.add_wf(fw)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        launch_rocket(self.lp, self.fworker)

        self.assertEqual(self.lp.launches.count(), 1)

    def test_add_wf_to_fws(self):
        fw1 = Firework([UpdateSpecTask()])
        fw2 = Firework([ModSpecTask()])
        self.lp.add_wf(Workflow([fw1, fw2]))
        self.assertEqual(self.lp.fireworks.count(), 2)
        launch_rocket(self.lp, self.fworker)
        launch_rocket(self.lp, self.fworker)
        self.assertEqual(self.lp.launches.count(), 2)
        self.assertEqual(self.lp.fireworks.count(), 3)  # due to detour

        new_wf = Workflow([Firework([ModSpecTask()])])
        self.lp.add_wf_to_fws(new_wf, [1, 2])
        launch_rocket(self.lp, self.fworker)  # launch detour
        launch_rocket(self.lp, self.fworker)  # launch new FW
        launch_rocket(self.lp, self.fworker)  # dummy launch
        new_fw = self.lp.get_fw_by_id(4)
        self.assertEqual(new_fw.spec['dummy1'], 1)
        self.assertEqual(new_fw.spec['dummy2'], [True])

        self.assertEqual(self.lp.launches.count(), 4)
        self.assertEqual(self.lp.fireworks.count(), 4)

        new_wf = Workflow([Firework([ModSpecTask()])])
        self.lp.add_wf_to_fws(new_wf, [4])
        launch_rocket(self.lp, self.fworker)  # launch new FW
        new_fw = self.lp.get_fw_by_id(5)
        self.assertEqual(new_fw.spec['dummy2'], [True])

        new_wf = Workflow([Firework([ModSpecTask()])])
        self.assertRaises(ValueError, self.lp.add_wf_to_fws, new_wf, [4], detour=True)

    def test_add_wf_to_fws_detour(self):
        fw1 = Firework([ModSpecTask()], fw_id=1)
        fw2 = Firework([ModSpecTask()], fw_id=2, parents=[fw1])
        self.lp.add_wf(Workflow([fw1, fw2]))

        new_wf = Workflow([Firework([ModSpecTask()])])
        self.lp.add_wf_to_fws(new_wf, [1], detour=True)

        launch_rocket(self.lp, self.fworker)
        launch_rocket(self.lp, self.fworker)

        self.assertEqual(self.lp.get_fw_by_id(2).spec['dummy2'], [True, True])


    def test_force_lock_removal(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {'store_stdout': True})
        fw = Firework(test1, {"_dupefinder": DupeFinderExact()}, fw_id=1)
        self.lp.add_wf(fw)
        self.assertEqual(WFLOCK_EXPIRATION_KILL, True)
        # add a manual lock
        with WFLock(self.lp, 1):
            with WFLock(self.lp, 1, expire_secs=1):
                self.assertTrue(True)  # dummy to make sure we got here

    def test_fizzle(self):
        p = PyTask(func="fireworks.tests.mongo_tests.throw_error", args=["Testing; this error is normal."])
        fw = Firework(p)
        self.lp.add_wf(fw)
        self.assertTrue(launch_rocket(self.lp, self.fworker))
        self.assertEqual(self.lp.get_fw_by_id(1).state, 'FIZZLED')
        self.assertFalse(launch_rocket(self.lp, self.fworker))

    def test_defuse(self):
        p = PyTask(func="fireworks.tests.mongo_tests.throw_error", args=["This should not happen"])
        fw = Firework(p)
        self.lp.add_wf(fw)
        self.lp.defuse_fw(fw.fw_id)
        self.assertFalse(launch_rocket(self.lp, self.fworker))

    def test_archive(self):
        p = PyTask(func="fireworks.tests.mongo_tests.throw_error", args=["This should not happen"])
        fw = Firework(p)
        self.lp.add_wf(fw)
        self.lp.archive_wf(fw.fw_id)
        self.assertFalse(launch_rocket(self.lp, self.fworker))

    def test_stats(self):
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {'store_stdout': True})
        fw = Firework(test1)
        self.lp.add_wf(fw)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        launch_rocket(self.lp, self.fworker)
        s=FWStats(self.lp)
        launch_results=s.get_launch_summary(time_field="updated_on")[0]
        self.assertEqual((launch_results["_id"],launch_results["count"]), ("COMPLETED", 2))
        self.lp.add_wf(fw)
        fireworks_results=s.get_fireworks_summary(time_field="updated_on")
        self.assertEqual((fireworks_results[1]["_id"], fireworks_results[1]["count"]), ("READY", 1))
        launch_rocket(self.lp, self.fworker)
        workflow_results=s.get_workflow_summary(time_field="updated_on")
        self.assertEqual((workflow_results[0]["_id"], workflow_results[0]["count"]), ("COMPLETED", 3))


if __name__ == "__main__":
    unittest.main()
