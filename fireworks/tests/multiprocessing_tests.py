import os
import pickle
import shutil
from unittest import TestCase
import unittest
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
        lp.reset('2014-04-23')
        lp.add_wf(FireWork(ScriptTask.from_str('echo "hello 1"')))
        lp.add_wf(FireWork(ScriptTask.from_str('echo "hello 2"')))
        launch_multiprocess(lp, FWorker(), 'DEBUG', 0, 2, 10)
        os.chdir(cur_dir)
        shutil.rmtree(scr_dir)


if __name__ == '__main__':
    unittest.main()