"""
import os
import pickle
import shutil
from unittest import TestCase
import unittest
import datetime
from fireworks import LaunchPad, FireWork, FWorker
from fireworks.core.firework import Workflow
from fireworks.features.multi_launcher import launch_multiprocess
from fireworks.user_objects.firetasks.script_task import ScriptTask

__author__ = 'xiaohuiqu'


class TestLinks(TestCase):
    def test_pickle(self):
        links1 = Workflow.Links({1: 2, 3: [5, 7, 8]})
        s = pickle.dumps(links1)
        links2 = pickle.loads(s)
        self.assertEqual(str(links1), str(links2))


class TestCheckoutFW(TestCase):
    def test_checkout_fw(self):
        cur_dir = os.getcwd()
        scr_dir = "launch_scratch"
        if not os.path.isdir(scr_dir):
            os.makedirs(scr_dir)
        os.chdir(scr_dir)
        lp = LaunchPad()
        lp.reset(password=None, require_password=False)
        lp.add_wf(FireWork(ScriptTask.from_str(
            shell_cmd='echo "hello 1"',
            parameters={"stdout_file": "task.out"}), fw_id=1))
        lp.add_wf(FireWork(ScriptTask.from_str(
            shell_cmd='echo "hello 2"',
            parameters={"stdout_file": "task.out"}), fw_id=2))
        launch_multiprocess(lp, FWorker(), 'DEBUG', 0, 2, 10)
        fw1 = lp.get_fw_by_id(1)
        fw2 = lp.get_fw_by_id(2)
        self.assertEqual(fw1.launches[0].state_history[-1]["state"],
                         "COMPLETED")
        self.assertEqual(fw2.launches[0].state_history[-1]["state"],
                         "COMPLETED")
        with open(os.path.join(fw1.launches[0].launch_dir, "task.out")) as f:
            task1out = f.readlines()
        self.assertEqual(task1out, ['hello 1\n'])
        with open(os.path.join(fw2.launches[0].launch_dir, "task.out")) as f:
            task2out = f.readlines()
        self.assertEqual(task2out, ['hello 2\n'])
        os.chdir(cur_dir)
        lp.reset(password=None, require_password=False)
        shutil.rmtree(scr_dir)


if __name__ == '__main__':
    unittest.main()
"""