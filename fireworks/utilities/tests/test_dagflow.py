"""Unit tests for the DAGFlow class."""

__author__ = "Ivan Kondov"
__copyright__ = "Copyright 2017, Karlsruhe Institute of Technology"
__email__ = "ivan.kondov@kit.edu"

import os
import unittest
import uuid

import pytest

from fireworks import Firework, PyTask, Workflow


class DAGFlowTest(unittest.TestCase):
    """run tests for DAGFlow class."""

    def setUp(self) -> None:
        try:
            __import__("igraph", fromlist=["Graph"])
        except (ImportError, ModuleNotFoundError):
            raise unittest.SkipTest("Skipping because python-igraph not installed")

        self.fw1 = Firework(
            PyTask(func="math.pow", inputs=["base", "exponent"], outputs=["first power"]),
            name="pow(2, 3)",
            spec={"base": 2, "exponent": 3},
        )
        self.fw2 = Firework(
            PyTask(func="math.pow", inputs=["first power", "exponent"], outputs=["second power"]),
            name="pow(pow(2, 3), 4)",
            spec={"exponent": 4},
        )
        self.fw3 = Firework(PyTask(func="print", inputs=["second power"]), name="the third one")

    def test_dagflow_ok(self) -> None:
        """Construct and replicate."""
        from fireworks.utilities.dagflow import DAGFlow

        wfl = Workflow([self.fw1, self.fw2, self.fw3], {self.fw1: [self.fw2], self.fw2: [self.fw3], self.fw3: []})
        dagf = DAGFlow.from_fireworks(wfl)
        DAGFlow(**dagf.to_dict())

    def test_dagflow_loop(self) -> None:
        """Loop in graph."""
        from fireworks.utilities.dagflow import DAGFlow

        wfl = Workflow([self.fw1, self.fw2, self.fw3], {self.fw1: self.fw2, self.fw2: self.fw3, self.fw3: self.fw1})
        msg = "The workflow graph must be a DAG.: found cycles:"
        with pytest.raises(AssertionError) as exc:
            DAGFlow.from_fireworks(wfl).check()
        assert msg in str(exc.value)

    def test_dagflow_cut(self) -> None:
        """Disconnected graph."""
        from fireworks.utilities.dagflow import DAGFlow

        wfl = Workflow([self.fw1, self.fw2, self.fw3], {self.fw1: self.fw2})
        msg = "The workflow graph must be connected"
        with pytest.raises(AssertionError) as exc:
            DAGFlow.from_fireworks(wfl).check()
        assert msg in str(exc.value)

    def test_dagflow_link(self) -> None:
        """Wrong links."""
        from fireworks.utilities.dagflow import DAGFlow

        wfl = Workflow([self.fw1, self.fw2, self.fw3], {self.fw1: [self.fw2, self.fw3]})
        msg = "Every input in inputs list must have exactly one source."
        with pytest.raises(AssertionError) as exc:
            DAGFlow.from_fireworks(wfl).check()
        assert msg in str(exc.value)

    def test_dagflow_missing_input(self) -> None:
        """Missing input."""
        from fireworks.utilities.dagflow import DAGFlow

        fw2 = Firework(
            PyTask(func="math.pow", inputs=["first power", "exponent"], outputs=["second power"]),
            name="pow(pow(2, 3), 4)",
        )
        wfl = Workflow([self.fw1, fw2], {self.fw1: [fw2], fw2: []})
        msg = (
            r"Every input in inputs list must have exactly one source.', 'step', "
            r"'pow(pow(2, 3), 4)', 'entity', 'exponent', 'sources', []"
        )
        with pytest.raises(AssertionError) as exc:
            DAGFlow.from_fireworks(wfl).check()
        assert msg in str(exc.value)

    def test_dagflow_clashing_inputs(self) -> None:
        """Parent firework output overwrites an input in spec."""
        from fireworks.utilities.dagflow import DAGFlow

        fw2 = Firework(
            PyTask(func="math.pow", inputs=["first power", "exponent"], outputs=["second power"]),
            name="pow(pow(2, 3), 4)",
            spec={"exponent": 4, "first power": 8},
        )
        wfl = Workflow([self.fw1, fw2], {self.fw1: [fw2], fw2: []})
        msg = (
            r"'Every input in inputs list must have exactly one source.', 'step', "
            r"'pow(pow(2, 3), 4)', 'entity', 'first power', 'sources'"
        )
        with pytest.raises(AssertionError) as exc:
            DAGFlow.from_fireworks(wfl).check()
        assert msg in str(exc.value)

    def test_dagflow_race_condition(self) -> None:
        """Two parent firework outputs overwrite each other."""
        from fireworks.utilities.dagflow import DAGFlow

        task = PyTask(func="math.pow", inputs=["base", "exponent"], outputs=["second power"])
        fw1 = Firework(task, name="pow(2, 3)", spec={"base": 2, "exponent": 3})
        fw2 = Firework(task, name="pow(2, 3)", spec={"base": 2, "exponent": 3})
        wfl = Workflow([fw1, fw2, self.fw3], {fw1: [self.fw3], fw2: [self.fw3]})
        msg = (
            r"'Every input in inputs list must have exactly one source.', 'step', "
            r"'the third one', 'entity', 'second power', 'sources', [0, 1]"
        )
        with pytest.raises(AssertionError) as exc:
            DAGFlow.from_fireworks(wfl).check()
        assert msg in str(exc.value)

    def test_dagflow_clashing_outputs(self) -> None:
        """Subsequent task overwrites output of a task."""
        from fireworks.utilities.dagflow import DAGFlow

        tasks = [
            PyTask(func="math.pow", inputs=["first power 1", "exponent"], outputs=["second power"]),
            PyTask(func="math.pow", inputs=["first power 2", "exponent"], outputs=["second power"]),
        ]
        fwk = Firework(tasks, spec={"exponent": 4, "first power 1": 8, "first power 2": 4})
        msg = "Several tasks may not use the same name in outputs list."
        with pytest.raises(AssertionError) as exc:
            DAGFlow.from_fireworks(Workflow([fwk], {})).check()
        assert msg in str(exc.value)

    def test_dagflow_non_dataflow_tasks(self) -> None:
        """non-dataflow tasks using outputs and inputs keys do not fail."""
        from fireworks.core.firework import FiretaskBase
        from fireworks.utilities.dagflow import DAGFlow

        class NonDataFlowTask(FiretaskBase):
            """a firetask class for testing."""

            _fw_name = "NonDataFlowTask"
            required_params = ["inputs", "outputs"]

            def run_task(self, fw_spec) -> None:
                pass

        task = NonDataFlowTask(inputs=["first power", "exponent"], outputs=["second power"])
        fw2 = Firework(task, spec={"exponent": 4, "first power": 8})
        wfl = Workflow([self.fw1, fw2], {self.fw1: [fw2], fw2: []})
        DAGFlow.from_fireworks(wfl).check()

    def test_dagflow_view(self) -> None:
        """Visualize the workflow graph."""
        from fireworks.utilities.dagflow import DAGFlow

        wfl = Workflow([self.fw1, self.fw2, self.fw3], {self.fw1: [self.fw2], self.fw2: [self.fw3], self.fw3: []})
        dagf = DAGFlow.from_fireworks(wfl)
        dagf.add_step_labels()
        filename = str(uuid.uuid4())
        dagf.to_dot(filename, view="combined")
        assert os.path.exists(filename)
        os.remove(filename)
        filename = str(uuid.uuid4())
        dagf.to_dot(filename, view="dataflow")
        assert os.path.exists(filename)
        os.remove(filename)
        filename = str(uuid.uuid4())
        dagf.to_dot(filename, view="controlflow")
        assert os.path.exists(filename)
        os.remove(filename)
