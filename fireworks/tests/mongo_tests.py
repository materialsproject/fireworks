import glob
import json
import os
import random
import shutil
import time
import unittest
from multiprocessing import Pool
from typing import NoReturn

import pytest

from fireworks import FWAction, explicit_serialize
from fireworks.core.firework import FiretaskBase, Firework, Workflow
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad, WFLock
from fireworks.core.rocket_launcher import launch_rocket, rapidfire
from fireworks.features.background_task import BackgroundTask
from fireworks.features.stats import FWStats
from fireworks.queue.queue_launcher import setup_offline_job
from fireworks.tests.tasks import DummyFWEnvTask, DummyJobPassTask, DummyLPTask
from fireworks.user_objects.dupefinders.dupefinder_exact import DupeFinderExact
from fireworks.user_objects.firetasks.fileio_tasks import FileTransferTask, FileWriteTask
from fireworks.user_objects.firetasks.script_task import PyTask, ScriptTask
from fireworks.user_objects.firetasks.templatewriter_task import TemplateWriterTask
from fw_tutorials.dynamic_wf.fibadd_task import FibonacciAdderTask
from fw_tutorials.firetask.addition_task import AdditionTask

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Mar 06, 2013"

TESTDB_NAME = "fireworks_unittest"
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
NCORES_PARALLEL_TEST = 4


def random_launch(lp_creds) -> None:
    lp = LaunchPad.from_dict(lp_creds)
    while lp.run_exists(None):
        launch_rocket(lp)
        time.sleep(random.random() / 3 + 0.1)


def throw_error(msg) -> NoReturn:
    raise ValueError(msg)


@explicit_serialize
class MultipleDetourTask(FiretaskBase):
    def run_task(self, fw_spec):
        print("Running the Multiple Detour Task")
        dt1 = Firework(ScriptTask.from_str('echo "this is intermediate job 1"'))
        dt2 = Firework(ScriptTask.from_str('echo "this is intermediate job 2"'))
        dt3 = Firework(ScriptTask.from_str('echo "this is intermediate job 3"'))
        return FWAction(detours=[dt1, dt2, dt3])


@explicit_serialize
class UpdateSpecTask(FiretaskBase):
    def run_task(self, fw_spec):
        print("Running the Update Spec Task")
        dt1 = Firework(ScriptTask.from_str('echo "this is dummy job 1"'))
        return FWAction(update_spec={"dummy1": 1}, additions=[dt1])


@explicit_serialize
class ModSpecTask(FiretaskBase):
    def run_task(self, fw_spec):
        print("Running the Mod Spec Task")
        return FWAction(mod_spec=[{"_push": {"dummy2": True}}])


class MongoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lp = None
        cls.fworker = FWorker()
        try:
            cls.lp = LaunchPad(name=TESTDB_NAME, strm_lvl="ERROR")
            cls.lp.reset(password=None, require_password=False)
        except Exception:
            raise unittest.SkipTest("MongoDB is not running in localhost:27017! Skipping tests.")

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

    @staticmethod
    def _teardown(dests) -> None:
        for f in dests:
            if os.path.exists(f):
                os.remove(f)

    def setUp(self) -> None:
        self.lp.reset(password=None, require_password=False)
        self.old_wd = os.getcwd()

    def tearDown(self) -> None:
        self.lp.reset(password=None, require_password=False)
        if os.path.exists(os.path.join("FW.json")):
            os.remove("FW.json")
        if os.path.exists(os.path.join("FW_offline.json")):
            os.remove("FW_offline.json")
        if os.path.exists(os.path.join("FW_ping.json")):
            os.remove("FW_ping.json")
        os.chdir(self.old_wd)
        for i in glob.glob(os.path.join(MODULE_DIR, "launcher*")):
            shutil.rmtree(i)

    def test_basic_fw(self) -> None:
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {"store_stdout": True})
        fw = Firework(test1)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        assert self.lp.get_launch_by_id(1).action.stored_data["stdout"] == "test1\n"

    def test_basic_fw_offline(self) -> None:
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {"store_stdout": True})
        fw = Firework(test1)
        self.lp.add_wf(fw)

        fw, launch_id = self.lp.reserve_fw(self.fworker, os.getcwd())

        setup_offline_job(self.lp, fw, launch_id)

        launch_rocket(None, self.fworker)

        with open(os.path.join(os.getcwd(), "FW_offline.json")) as f:
            fwo = json.load(f)
            assert fwo["state"] == "COMPLETED"
            assert fwo["launch_id"] == 1
            assert fwo["fwaction"] == {
                "update_spec": {},
                "mod_spec": [],
                "stored_data": {"returncode": 0, "stdout": "test1\n", "all_returncodes": [0]},
                "exit": False,
                "detours": [],
                "additions": [],
                "defuse_children": False,
                "defuse_workflow": False,
                "propagate": False,
            }

        with open(os.path.join(os.getcwd(), "FW_ping.json")) as f:
            fwp = json.load(f)
            assert fwp["ping_time"] is not None

        launch = self.lp.offline_runs.find_one({"completed": False, "deprecated": False}, {"launch_id": 1})
        self.lp.recover_offline(launch["launch_id"])
        assert self.lp.get_launch_by_id(1).action.stored_data["stdout"] == "test1\n"

    def test_offline_fw_passinfo(self) -> None:
        fw1 = Firework([AdditionTask()], {"input_array": [1, 1]}, name="1")
        fw2 = Firework([AdditionTask()], {"input_array": [2, 2]}, name="2")
        fw3 = Firework([AdditionTask()], {"input_array": [3]}, parents=[fw1, fw2], name="3")

        wf = Workflow([fw1, fw2, fw3])
        self.lp.add_wf(wf)

        # make dirs for launching jobs
        cur_dir = os.path.dirname(os.path.abspath(__file__))

        os.mkdir(os.path.join(cur_dir, "launcher_1"))
        os.mkdir(os.path.join(cur_dir, "launcher_2"))
        os.mkdir(os.path.join(cur_dir, "launcher_3"))

        # launch two parent jobs
        os.chdir(os.path.join(cur_dir, "launcher_1"))
        fw, launch_id = self.lp.reserve_fw(self.fworker, os.getcwd())
        setup_offline_job(self.lp, fw, launch_id)
        launch_rocket(None, self.fworker)

        os.chdir(os.path.join(cur_dir, "launcher_2"))
        fw, launch_id = self.lp.reserve_fw(self.fworker, os.getcwd())
        setup_offline_job(self.lp, fw, launch_id)
        launch_rocket(None, self.fworker)

        # recover jobs
        for launch in self.lp.offline_runs.find({"completed": False, "deprecated": False}, {"launch_id": 1}):
            fw = self.lp.recover_offline(launch["launch_id"])

        # launch child job
        os.chdir(os.path.join(cur_dir, "launcher_3"))
        fw, launch_id = self.lp.reserve_fw(self.fworker, os.getcwd())
        last_fw_id = fw.fw_id
        setup_offline_job(self.lp, fw, launch_id)
        launch_rocket(None, self.fworker)

        # recover jobs
        for launch in self.lp.offline_runs.find({"completed": False, "deprecated": False}, {"launch_id": 1}):
            fw = self.lp.recover_offline(launch["launch_id"])

        # confirm the sum in the child job
        child_fw = self.lp.get_fw_by_id(last_fw_id)
        assert set(child_fw.spec["input_array"]) == {2, 3, 4}
        assert child_fw.launches[0].action.stored_data["sum"] == 9

    def test_multi_fw(self) -> None:
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {"store_stdout": True})
        test2 = ScriptTask.from_str("python -c 'print(\"test2\")'", {"store_stdout": True})
        fw = Firework([test1, test2])
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        assert self.lp.get_launch_by_id(1).action.stored_data["stdout"] == "test2\n"

    def test_multi_fw_complex(self) -> None:
        dest1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inputs.txt")
        dest2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_file.txt")
        self._teardown([dest1, dest2])
        try:
            # create the Firework consisting of multiple tasks
            firetask1 = TemplateWriterTask(
                {
                    "context": {"opt1": 5.0, "opt2": "fast method"},
                    "template_file": "simple_template.txt",
                    "output_file": dest1,
                }
            )
            firetask2 = FileTransferTask({"files": [{"src": dest1, "dest": dest2}], "mode": "copy"})
            fw = Firework([firetask1, firetask2])

            # store workflow and launch it locally, single shot
            self.lp.add_wf(fw)
            launch_rocket(self.lp, self.fworker)

            # read inputs.txt, words.txt, dest
            for d in [dest1, dest2]:
                with open(d) as f:
                    assert f.read() == "option1 = 5.0\noption2 = fast method"

        finally:
            self._teardown([dest1, dest2])

    def test_backgroundtask(self) -> None:
        dest1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hello.txt")
        self._teardown([dest1])

        try:
            test1 = ScriptTask.from_str("python -c 'print(\"testing background...\")'", {"store_stdout": True})

            bg_task1 = BackgroundTask(
                FileWriteTask({"files_to_write": [{"filename": dest1, "contents": "hello"}]}),
                num_launches=1,
                run_on_finish=True,
            )
            fw = Firework(test1, spec={"_background_tasks": [bg_task1]})
            self.lp.add_wf(fw)
            launch_rocket(self.lp, self.fworker)

            with open(dest1) as f:
                assert f.read() == "hello"

        finally:
            self._teardown([dest1])

    def test_add_fw(self) -> None:
        fw = Firework(AdditionTask(), {"input_array": [5, 7]})
        self.lp.add_wf(fw)
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)
        assert self.lp.get_launch_by_id(1).action.stored_data["sum"] == 12

    def test_org_wf(self) -> None:
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {"store_stdout": True})
        test2 = ScriptTask.from_str("python -c 'print(\"test2\")'", {"store_stdout": True})
        fw1 = Firework(test1, fw_id=-1)
        fw2 = Firework(test2, fw_id=-2)
        wf = Workflow([fw1, fw2], {-1: -2})
        self.lp.add_wf(wf)
        launch_rocket(self.lp, self.fworker)
        assert self.lp.get_launch_by_id(1).action.stored_data["stdout"] == "test1\n"
        launch_rocket(self.lp, self.fworker)
        assert self.lp.get_launch_by_id(2).action.stored_data["stdout"] == "test2\n"

    def test_fibadder(self) -> None:
        fib = FibonacciAdderTask()
        fw = Firework(fib, {"smaller": 0, "larger": 1, "stop_point": 3})
        self.lp.add_wf(fw)
        rapidfire(self.lp, self.fworker, m_dir=MODULE_DIR)

        assert self.lp.get_launch_by_id(1).action.stored_data["next_fibnum"] == 1
        assert self.lp.get_launch_by_id(2).action.stored_data["next_fibnum"] == 2
        assert self.lp.get_launch_by_id(3).action.stored_data == {}
        assert not self.lp.run_exists()

    def test_parallel_fibadder(self) -> None:
        # this is really testing to see if a Workflow can handle multiple FWs updating it at once
        parent = Firework(ScriptTask.from_str("python -c 'print(\"test1\")'", {"store_stdout": True}))
        fib1 = Firework(FibonacciAdderTask(), {"smaller": 0, "larger": 1, "stop_point": 30}, parents=[parent])
        fib2 = Firework(FibonacciAdderTask(), {"smaller": 0, "larger": 1, "stop_point": 30}, parents=[parent])
        fib3 = Firework(FibonacciAdderTask(), {"smaller": 0, "larger": 1, "stop_point": 30}, parents=[parent])
        fib4 = Firework(FibonacciAdderTask(), {"smaller": 0, "larger": 1, "stop_point": 30}, parents=[parent])
        wf = Workflow([parent, fib1, fib2, fib3, fib4])
        self.lp.add_wf(wf)

        p = Pool(NCORES_PARALLEL_TEST)

        creds_array = [self.lp.to_dict()] * NCORES_PARALLEL_TEST
        p.map(random_launch, creds_array)

    def test_multi_detour(self) -> None:
        fw1 = Firework([MultipleDetourTask()], fw_id=1)
        fw2 = Firework([ScriptTask.from_str('echo "DONE"')], parents=[fw1], fw_id=2)
        self.lp.add_wf(Workflow([fw1, fw2]))
        rapidfire(self.lp)
        links = self.lp.get_wf_by_fw_id(1).links
        assert set(links[1]) == {2, 3, 4, 5}
        assert set(links[2]) == set()
        assert set(links[3]) == {2}
        assert set(links[4]) == {2}
        assert set(links[5]) == {2}

    def test_fw_env(self) -> None:
        t = DummyFWEnvTask()
        fw = Firework(t)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        assert self.lp.get_launch_by_id(1).action.stored_data["data"] == "hello"
        self.lp.add_wf(fw)
        launch_rocket(self.lp, FWorker(env={"hello": "world"}))
        assert self.lp.get_launch_by_id(2).action.stored_data["data"] == "world"

    def test_job_info(self) -> None:
        fw1 = Firework([ScriptTask.from_str('echo "Testing job info"')], spec={"_pass_job_info": True}, fw_id=1)
        fw2 = Firework([DummyJobPassTask()], parents=[fw1], spec={"_pass_job_info": True, "target": 1}, fw_id=2)
        fw3 = Firework([DummyJobPassTask()], parents=[fw2], spec={"target": 2}, fw_id=3)
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

        assert modified_spec["_job_info"] is not None
        assert modified_spec["_job_info"][0]["launch_dir"] is not None
        assert modified_spec["_job_info"][0]["name"] == "Unnamed FW"
        assert modified_spec["_job_info"][0]["fw_id"] == 1

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

        assert len(modified_spec["_job_info"]) == 2

    def test_files_in_out(self) -> None:
        # create the Workflow that passes files_in and files_out
        fw1 = Firework(
            [ScriptTask.from_str('echo "This is the first FireWork" > test1')],
            spec={"_files_out": {"fwtest1": "test1"}},
            fw_id=1,
        )
        fw2 = Firework(
            [ScriptTask.from_str("gzip hello")],
            fw_id=2,
            parents=[fw1],
            spec={"_files_in": {"fwtest1": "hello"}, "_files_out": {"fw2": "hello.gz"}},
        )
        fw3 = Firework(
            [ScriptTask.from_str("cat fwtest.2")], fw_id=3, parents=[fw2], spec={"_files_in": {"fw2": "fwtest.2"}}
        )
        wf = Workflow([fw1, fw2, fw3], {fw1: [fw2], fw2: [fw3]})

        # store workflow and launch it locally
        self.lp.add_wf(wf)
        launch_rocket(self.lp, self.fworker)
        assert os.path.exists("test1")
        launch_rocket(self.lp, self.fworker)
        assert os.path.exists("hello.gz")
        launch_rocket(self.lp, self.fworker)
        assert os.path.exists("fwtest.2")
        for f in ["test1", "hello.gz", "fwtest.2"]:
            os.remove(f)

    def test_preserve_fworker(self) -> None:
        fw1 = Firework(
            [ScriptTask.from_str('echo "Testing preserve FWorker"')], spec={"_preserve_fworker": True}, fw_id=1
        )
        fw2 = Firework(
            [ScriptTask.from_str('echo "Testing preserve FWorker pt 2"')], spec={"target": 1}, parents=[fw1], fw_id=2
        )
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

        assert modified_spec["_fworker"] is not None

    def test_add_lp_and_fw_id(self) -> None:
        fw1 = Firework([DummyLPTask()], spec={"_add_launchpad_and_fw_id": True})
        self.lp.add_wf(fw1)
        launch_rocket(self.lp, self.fworker)
        assert self.lp.get_launch_by_id(1).action.stored_data["fw_id"] == 1
        assert self.lp.get_launch_by_id(1).action.stored_data["host"] is not None

    def test_spec_copy(self) -> None:
        task1 = ScriptTask.from_str('echo "Task 1"')
        task2 = ScriptTask.from_str('echo "Task 2"')

        spec = {"_category": "dummy_category"}

        fw1 = Firework(task1, fw_id=1, name="Task 1", spec=spec)
        fw2 = Firework(task2, fw_id=2, name="Task 2", spec=spec)

        self.lp.add_wf(Workflow([fw1, fw2]))

        assert self.lp.get_fw_by_id(1).tasks[0]["script"][0] == 'echo "Task 1"'
        assert self.lp.get_fw_by_id(2).tasks[0]["script"][0] == 'echo "Task 2"'

    def test_category(self) -> None:
        task1 = ScriptTask.from_str('echo "Task 1"')
        task2 = ScriptTask.from_str('echo "Task 2"')

        spec = {"_category": "dummy_category"}

        fw1 = Firework(task1, fw_id=1, name="Task 1", spec=spec)
        fw2 = Firework(task2, fw_id=2, name="Task 2", spec=spec)

        self.lp.add_wf(Workflow([fw1, fw2]))

        assert self.lp.run_exists(FWorker(category="dummy_category"))
        assert not self.lp.run_exists(FWorker(category="other category"))
        assert not self.lp.run_exists(FWorker(category="__none__"))
        assert self.lp.run_exists(FWorker())  # can run any category
        assert self.lp.run_exists(FWorker(category=["dummy_category", "other category"]))

    def test_category_pt2(self) -> None:
        task1 = ScriptTask.from_str('echo "Task 1"')
        task2 = ScriptTask.from_str('echo "Task 2"')

        fw1 = Firework(task1, fw_id=1, name="Task 1")
        fw2 = Firework(task2, fw_id=2, name="Task 2")

        self.lp.add_wf(Workflow([fw1, fw2]))

        assert not self.lp.run_exists(FWorker(category="dummy_category"))
        assert self.lp.run_exists(FWorker(category="__none__"))
        assert self.lp.run_exists(FWorker())  # can run any category
        assert not self.lp.run_exists(FWorker(category=["dummy_category", "other category"]))

    def test_delete_fw(self) -> None:
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {"store_stdout": True})
        fw = Firework(test1)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        assert self.lp.get_launch_by_id(1).action.stored_data["stdout"] == "test1\n"
        self.lp.delete_wf(fw.fw_id)
        with pytest.raises(ValueError):
            self.lp.get_fw_by_id(fw.fw_id)
        with pytest.raises(ValueError):
            self.lp.get_launch_by_id(1)

    def test_duplicate_delete_fw(self) -> None:
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {"store_stdout": True})
        fw = Firework(test1, {"_dupefinder": DupeFinderExact()})
        self.lp.add_wf(fw)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        # TODO: if test keeps failing on Travis, add an explicit check of nlaunches>0 in the database here
        # this will ensure the first Rocket is actually in the DB
        launch_rocket(self.lp, self.fworker)

        run_id = self.lp.get_launch_by_id(1).fw_id
        del_id = 1 if run_id == 2 else 2
        self.lp.delete_wf(del_id)
        with pytest.raises(ValueError):
            self.lp.get_fw_by_id(del_id)
        assert self.lp.get_launch_by_id(1).action.stored_data["stdout"] == "test1\n"

    def test_dupefinder(self) -> None:
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {"store_stdout": True})
        fw = Firework(test1, {"_dupefinder": DupeFinderExact()})
        self.lp.add_wf(fw)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        # TODO: if test keeps failing on Travis, add an explicit check of nlaunches>0 in the database here
        # this will ensure the first Rocket is actually in the DB
        launch_rocket(self.lp, self.fworker)

        time.sleep(1)

        if self.lp.launches.count_documents({}) > 1:
            print("TOO MANY LAUNCHES FOUND!")
            print("--------")
            for d in self.lp.launches.find():
                print(d)
            print("--------")
        assert self.lp.launches.count_documents({}) == 1

    def test_append_wf(self) -> None:
        fw1 = Firework([UpdateSpecTask()])
        fw2 = Firework([ModSpecTask()])
        self.lp.add_wf(Workflow([fw1, fw2]))
        assert self.lp.fireworks.count_documents({}) == 2
        launch_rocket(self.lp, self.fworker)
        launch_rocket(self.lp, self.fworker)
        assert self.lp.launches.count_documents({}) == 2
        assert self.lp.fireworks.count_documents({}) == 3  # due to detour

        new_wf = Workflow([Firework([ModSpecTask()])])
        self.lp.append_wf(new_wf, [1, 2])
        launch_rocket(self.lp, self.fworker)  # launch detour
        launch_rocket(self.lp, self.fworker)  # launch new FW
        launch_rocket(self.lp, self.fworker)  # dummy launch
        new_fw = self.lp.get_fw_by_id(4)
        assert new_fw.spec["dummy1"] == 1
        assert new_fw.spec["dummy2"] == [True]

        assert self.lp.launches.count_documents({}) == 4
        assert self.lp.fireworks.count_documents({}) == 4

        new_wf = Workflow([Firework([ModSpecTask()])])
        self.lp.append_wf(new_wf, [4])
        launch_rocket(self.lp, self.fworker)  # launch new FW
        new_fw = self.lp.get_fw_by_id(5)
        assert new_fw.spec["dummy2"] == [True]

        new_wf = Workflow([Firework([ModSpecTask()])])
        with pytest.raises(ValueError, match="Cannot append to a FW that is not in the original Workflow"):
            self.lp.append_wf(new_wf, [4], detour=True)

    def test_append_wf_detour(self) -> None:
        fw1 = Firework([ModSpecTask()], fw_id=1)
        fw2 = Firework([ModSpecTask()], fw_id=2, parents=[fw1])
        self.lp.add_wf(Workflow([fw1, fw2]))

        new_wf = Workflow([Firework([ModSpecTask()])])
        self.lp.append_wf(new_wf, [1], detour=True)

        launch_rocket(self.lp, self.fworker)
        launch_rocket(self.lp, self.fworker)

        assert self.lp.get_fw_by_id(2).spec["dummy2"] == [True, True]

    def test_force_lock_removal(self) -> None:
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {"store_stdout": True})
        fw = Firework(test1, {"_dupefinder": DupeFinderExact()}, fw_id=1)
        self.lp.add_wf(fw)
        # add a manual lock
        with WFLock(self.lp, 1), WFLock(self.lp, 1, kill=True, expire_secs=1):
            assert True  # dummy to make sure we got here

    def test_fizzle(self) -> None:
        p = PyTask(func="fireworks.tests.mongo_tests.throw_error", args=["Testing; this error is normal."])
        fw = Firework(p)
        self.lp.add_wf(fw)
        assert launch_rocket(self.lp, self.fworker)
        assert self.lp.get_fw_by_id(1).state == "FIZZLED"
        assert not launch_rocket(self.lp, self.fworker)

    def test_defuse(self) -> None:
        p = PyTask(func="fireworks.tests.mongo_tests.throw_error", args=["This should not happen"])
        fw = Firework(p)
        self.lp.add_wf(fw)
        self.lp.defuse_fw(fw.fw_id)
        assert not launch_rocket(self.lp, self.fworker)

    def test_archive(self) -> None:
        p = PyTask(func="fireworks.tests.mongo_tests.throw_error", args=["This should not happen"])
        fw = Firework(p)
        self.lp.add_wf(fw)
        self.lp.archive_wf(fw.fw_id)
        assert not launch_rocket(self.lp, self.fworker)

    def test_stats(self) -> None:
        test1 = ScriptTask.from_str("python -c 'print(\"test1\")'", {"store_stdout": True})
        fw = Firework(test1)
        self.lp.add_wf(fw)
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        launch_rocket(self.lp, self.fworker)
        s = FWStats(self.lp)
        launch_results = s.get_launch_summary(time_field="updated_on")[0]
        assert (launch_results["_id"], launch_results["count"]) == ("COMPLETED", 2)
        self.lp.add_wf(fw)
        fireworks_results = s.get_fireworks_summary(time_field="updated_on")
        assert (fireworks_results[1]["_id"], fireworks_results[1]["count"]) == ("READY", 1)
        launch_rocket(self.lp, self.fworker)
        workflow_results = s.get_workflow_summary(time_field="updated_on")
        assert (workflow_results[0]["_id"], workflow_results[0]["count"]) == ("COMPLETED", 3)
