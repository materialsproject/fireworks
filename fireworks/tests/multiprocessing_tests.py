# coding: utf-8

from __future__ import unicode_literals

import glob
import os
import pickle
import shutil
import unittest
from unittest import TestCase

from fireworks import LaunchPad, Firework, FWorker
from fireworks.core.firework import Workflow
from fireworks.features.multi_launcher import launch_multiprocess
from fireworks.user_objects.firetasks.script_task import ScriptTask


__author__ = 'xiaohuiqu'

TESTDB_NAME = 'job_packing_unittest'
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class TestLinks(TestCase):
    def test_pickle(self):
        links1 = Workflow.Links({1: 2, 3: [5, 7, 8]})
        s = pickle.dumps(links1)
        links2 = pickle.loads(s)
        self.assertEqual(str(links1), str(links2))


class TestCheckoutFW(TestCase):
    lp = None

    @classmethod
    def setUpClass(cls):
        cls.fworker = FWorker()
        try:
            cls.lp = LaunchPad(name=TESTDB_NAME, strm_lvl='ERROR')
            cls.lp.reset(password=None, require_password=False)
        except:
            raise unittest.SkipTest('MongoDB is not running in localhost:'
                                    '27017! Skipping tests.')

    @classmethod
    def tearDownClass(cls):
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

    def setUp(self):
        self.old_wd = os.getcwd()

    def tearDown(self):
        self.lp.reset(password=None, require_password=False)
        os.chdir(self.old_wd)
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        # noinspection PyUnresolvedReferences
        for i in glob.glob(os.path.join(MODULE_DIR, "launcher*")):
            shutil.rmtree(i)

    def test_checkout_fw(self):
        os.chdir(MODULE_DIR)
        self.lp.add_wf(Firework(ScriptTask.from_str(
            shell_cmd='echo "hello 1"',
            parameters={"stdout_file": "task.out"}), fw_id=1))
        self.lp.add_wf(Firework(ScriptTask.from_str(
            shell_cmd='echo "hello 2"',
            parameters={"stdout_file": "task.out"}), fw_id=2))
        launch_multiprocess(self.lp, FWorker(), 'DEBUG', 0, 2, 10)
        fw1 = self.lp.get_fw_by_id(1)
        fw2 = self.lp.get_fw_by_id(2)
        self.assertEqual(fw1.launches[0].state_history[-1]["state"],
                         "COMPLETED")
        self.assertEqual(fw2.launches[0].state_history[-1]["state"],
                         "COMPLETED")
        with open(os.path.join(fw1.launches[0].launch_dir, "task.out")) as f:
            self.assertEqual(f.readlines(), ['hello 1\n'])
        with open(os.path.join(fw2.launches[0].launch_dir, "task.out")) as f:
            self.assertEqual(f.readlines(), ['hello 2\n'])


class TestEarlyExit(TestCase):
    lp = None

    @classmethod
    def setUpClass(cls):
        cls.fworker = FWorker()
        try:
            cls.lp = LaunchPad(name=TESTDB_NAME, strm_lvl='ERROR')
            cls.lp.reset(password=None, require_password=False)
        except:
            raise unittest.SkipTest('MongoDB is not running in localhost:'
                                    '27017! Skipping tests.')

    @classmethod
    def tearDownClass(cls):
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

    def setUp(self):
        self.old_wd = os.getcwd()

    def tearDown(self):
        self.lp.reset(password=None, require_password=False)
        os.chdir(self.old_wd)
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        # noinspection PyUnresolvedReferences
        for i in glob.glob(os.path.join(MODULE_DIR, "launcher*")):
            shutil.rmtree(i)

    def test_early_exit(self):
        os.chdir(MODULE_DIR)
        script_text = "echo hello from process $PPID; sleep 2"
        fw1 = Firework(ScriptTask.from_str(shell_cmd=script_text,
                                           parameters={"stdout_file": "task.out"}),
                       fw_id=1)
        fw2 = Firework(ScriptTask.from_str(shell_cmd=script_text,
                                           parameters={"stdout_file": "task.out"}),
                       fw_id=2)
        fw3 = Firework(ScriptTask.from_str(shell_cmd=script_text,
                                           parameters={"stdout_file": "task.out"}),
                       fw_id=3)
        fw4 = Firework(ScriptTask.from_str(shell_cmd=script_text,
                                           parameters={"stdout_file": "task.out"}),
                       fw_id=4)
        wf = Workflow([fw1, fw2, fw3, fw4], {1: [2, 3], 2: [4], 3: [4]})
        self.lp.add_wf(wf)
        launch_multiprocess(self.lp, FWorker(), 'DEBUG', 0, 2, sleep_time=0.5)
        fw2 = self.lp.get_fw_by_id(2)
        fw3 = self.lp.get_fw_by_id(3)
        with open(os.path.join(fw2.launches[0].launch_dir, "task.out")) as f:
            fw2_text = f.read()
        with open(os.path.join(fw3.launches[0].launch_dir, "task.out")) as f:
            fw3_text = f.read()
        self.assertNotEqual(fw2_text, fw3_text)

if __name__ == '__main__':
    unittest.main()
