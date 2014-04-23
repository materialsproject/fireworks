import pickle
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


    def test_checkout_fw(self):
        lp = LaunchPad()
        lp.reset('2014-04-23')

        lp.add_wf(FireWork(ScriptTask.from_str('echo "hello 1"')))
        lp.add_wf(FireWork(ScriptTask.from_str('echo "hello 2"')))

        launch_multiprocess(lp, FWorker(), 'DEBUG', 0, 2, 10)


if __name__ == '__main__':
    unittest.main()