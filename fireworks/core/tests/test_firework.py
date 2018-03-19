# coding: utf-8

from __future__ import unicode_literals, division

"""
TODO: Modify unittest doc.
"""


__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__date__ = "2/26/14"

import unittest

from fireworks.core.firework import Firework, Workflow, FiretaskBase, FWAction
from fireworks.user_objects.firetasks.script_task import PyTask
from fireworks.utilities.fw_utilities import explicit_serialize


class FiretaskBaseTest(unittest.TestCase):

    def test_init(self):
        class DummyTask(FiretaskBase):

            required_params = ["hello"]

            def run_task(self, fw_spec):
                return self["hello"]

        with self.assertRaises(ValueError):
            DummyTask()
        d = DummyTask(hello="world")
        self.assertEqual(d.run_task({}), "world")
        d = DummyTask({"hello": "world2"})
        self.assertEqual(d.run_task({}), "world2")

        class DummyTask2(FiretaskBase):

            pass

        d = DummyTask2()
        self.assertRaises(NotImplementedError, d.run_task, {})


class PickleTask(FiretaskBase):
    required_params = ["test"]

    def run_task(self, fw_spec):
        return self["test"]


class FiretaskPickleTest(unittest.TestCase):
    def setUp(self):
        import pickle
        self.task = PickleTask(test=0)
        self.pkl_task = pickle.dumps(self.task)
        self.upkl_task = pickle.loads(self.pkl_task)

    def test_init(self):
        self.assertIsInstance(self.upkl_task, PickleTask)
        self.assertEqual(PickleTask.from_dict(self.task.to_dict()), self.upkl_task)
        self.assertEqual(dir(self.task), dir(self.upkl_task))

        result_task = self.task.run_task({})
        result_upkl_task = self.upkl_task.run_task({})
        self.assertEqual(result_task, result_upkl_task)


@explicit_serialize
class Task1(FiretaskBase):
    def run_task(self, fw_spec):
        print("task1", fw_spec)
        return FWAction(stored_data={"color": "red"})


@explicit_serialize
class Task2(FiretaskBase):
    def run_task(self, fw_spec):
        print("task2", fw_spec)
        return FWAction(stored_data={"color": "yellow"})


class WorkflowTest(unittest.TestCase):

    def setUp(self):
        self.fw1 = Firework(Task1())
        self.fw2 = Firework([Task2(), Task2()], parents=self.fw1)
        self.fw3 = Firework(Task1(), parents=self.fw1)

    def test_init(self):

        fws = []
        for i in range(5):
            fw = Firework([PyTask(func="print", args=[i])], fw_id=i)

            fws.append(fw)
        wf = Workflow(fws, links_dict={0: [1, 2, 3], 1: [4], 2: [4]})
        self.assertIsInstance(wf, Workflow)
        self.assertRaises(ValueError, Workflow, fws,
                          links_dict={0: [1, 2, 3], 1: [4], 100: [4]})
        self.assertRaises(ValueError, Workflow, fws,
                          links_dict={0: [1, 2, 3], 1: [4], 2: [100]})


    def test_copy(self):
        """Test that we can produce a copy of a Workflow but that the copy
        has unique fw_ids.

        """
        fws = []
        for i in range(5):
            fw = Firework([PyTask(func="print", args=[i])], fw_id=i,
                          name=i)
            fws.append(fw)

        wf = Workflow(fws, links_dict={0: [1, 2, 3], 1: [4], 2: [4]})

        wf_copy = Workflow.from_wflow(wf)
        
        # now we compare to the original to make sure dependencies are same.
        # have to do gymnastics because ids will NOT be the same
        # but names are retained
        for fw in wf_copy.fws:
            children = wf_copy.links.get(fw.fw_id, list())
            orig_id = fw.name

            orig_children = wf.links.get(orig_id, list())

            for child_id, orig_child_id in zip(children, orig_children):
                self.assertEqual(orig_child_id, wf_copy.id_fw[child_id].name)

    def test_remove_leaf_fws(self):
        fw4 = Firework(Task1(), parents=[self.fw2, self.fw3])
        fws = [self.fw1, self.fw2, self.fw3, fw4]
        wflow = Workflow(fws)
        leaf_ids = wflow.leaf_fw_ids
        parents = []
        for i in leaf_ids:
            parents.extend(wflow.links.parent_links[i])
        wflow.remove_fws(wflow.leaf_fw_ids)
        self.assertEqual(wflow.leaf_fw_ids, parents)

    def test_remove_root_fws(self):
        fw4 = Firework(Task1(), parents=[self.fw2, self.fw3])
        fws = [self.fw1, self.fw2, self.fw3, fw4]
        wflow = Workflow(fws)
        root_ids = wflow.root_fw_ids
        children = []
        for i in root_ids:
            children.extend(wflow.links[i])
        wflow.remove_fws(wflow.root_fw_ids)
        self.assertEqual(sorted(wflow.root_fw_ids), sorted(children))


if __name__ == '__main__':
    unittest.main()
