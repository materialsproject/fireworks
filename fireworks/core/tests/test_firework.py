"""TODO: Modify unittest doc."""

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__date__ = "2/26/14"

import unittest

import pytest

from fireworks.core.firework import FiretaskBase, Firework, FWAction, Workflow
from fireworks.user_objects.firetasks.script_task import PyTask
from fireworks.utilities.fw_utilities import explicit_serialize


class FiretaskBaseTest(unittest.TestCase):
    def test_init(self) -> None:
        class DummyTask(FiretaskBase):
            required_params = ["hello"]

            def run_task(self, fw_spec):
                return self["hello"]

        with pytest.raises(RuntimeError):
            DummyTask()
        d = DummyTask(hello="world")
        assert d.run_task({}) == "world"
        d = DummyTask({"hello": "world2"})
        assert d.run_task({}) == "world2"

        class DummyTask2(FiretaskBase):
            pass

        d = DummyTask2()
        with pytest.raises(NotImplementedError):
            d.run_task({})

    def test_param_checks(self) -> None:
        class DummyTask(FiretaskBase):
            _fw_name = "DummyTask"
            required_params = ["param1"]
            optional_params = ["param2"]

        with pytest.raises(RuntimeError):
            DummyTask(param2=3)  # missing required param
        with pytest.raises(RuntimeError):
            DummyTask(param1=3, param3=5)  # extraneous param
        DummyTask(param1=1)  # OK
        DummyTask(param1=1, param2=1)  # OK


class PickleTask(FiretaskBase):
    required_params = ["test"]

    def run_task(self, fw_spec):
        return self["test"]


class FiretaskPickleTest(unittest.TestCase):
    def setUp(self) -> None:
        import pickle

        self.task = PickleTask(test=0)
        self.pkl_task = pickle.dumps(self.task)
        self.upkl_task = pickle.loads(self.pkl_task)

    def test_init(self) -> None:
        assert isinstance(self.upkl_task, PickleTask)
        assert PickleTask.from_dict(self.task.to_dict()) == self.upkl_task
        assert dir(self.task) == dir(self.upkl_task)

        result_task = self.task.run_task({})
        result_upkl_task = self.upkl_task.run_task({})
        assert result_task == result_upkl_task


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
    def setUp(self) -> None:
        self.fw1 = Firework(Task1())
        self.fw2 = Firework([Task2(), Task2()], parents=self.fw1)
        self.fw3 = Firework(Task1(), parents=self.fw1)

    def test_init(self) -> None:
        fws = []
        for i in range(5):
            fw = Firework([PyTask(func="print", args=[i])], fw_id=i)

            fws.append(fw)
        wf = Workflow(fws, links_dict={0: [1, 2, 3], 1: [4], 2: [4]})
        assert isinstance(wf, Workflow)
        with pytest.raises(ValueError):
            Workflow(fws, links_dict={0: [1, 2, 3], 1: [4], 100: [4]})
        with pytest.raises(ValueError):
            Workflow(fws, links_dict={0: [1, 2, 3], 1: [4], 2: [100]})

    def test_copy(self) -> None:
        """Test that we can produce a copy of a Workflow but that the copy
        has unique fw_ids.
        """
        fws = []
        for i in range(5):
            fw = Firework([PyTask(func="print", args=[i])], fw_id=i, name=str(i))
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
                assert orig_child_id == wf_copy.id_fw[child_id].name

    def test_remove_leaf_fws(self) -> None:
        fw4 = Firework(Task1(), parents=[self.fw2, self.fw3])
        fws = [self.fw1, self.fw2, self.fw3, fw4]
        wflow = Workflow(fws)
        leaf_ids = wflow.leaf_fw_ids
        parents = []
        for i in leaf_ids:
            parents.extend(wflow.links.parent_links[i])
        wflow.remove_fws(wflow.leaf_fw_ids)
        assert wflow.leaf_fw_ids == parents

    def test_remove_root_fws(self) -> None:
        fw4 = Firework(Task1(), parents=[self.fw2, self.fw3])
        fws = [self.fw1, self.fw2, self.fw3, fw4]
        wflow = Workflow(fws)
        root_ids = wflow.root_fw_ids
        children = []
        for i in root_ids:
            children.extend(wflow.links[i])
        wflow.remove_fws(wflow.root_fw_ids)
        assert sorted(wflow.root_fw_ids) == sorted(children)

    def test_iter_len_index(self) -> None:
        fws = [self.fw1, self.fw2, self.fw3]
        wflow = Workflow(fws)
        for idx, fw in enumerate(wflow):
            assert fw == fws[idx]

        assert len(wflow) == len(fws)

        assert wflow[0] == self.fw1
