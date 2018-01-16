""" Unit tests for the DAGFlow class """

__author__ = 'Ivan Kondov'
__copyright__ = 'Copyright 2017, Karlsruhe Institute of Technology'
__email__ = 'ivan.kondov@kit.edu'

import os
import uuid
import unittest
from fireworks import PyTask, Firework, Workflow

class DAGFlowTest(unittest.TestCase):
    """ run tests for DAGFlow class """

    def setUp(self):
        try:
            from fireworks.utilities.dagflow import DAGFlow
        except:
            raise unittest.SkipTest("Skipping test, DagFlow not installed")

        self.fw1 = Firework(
            PyTask(
                func='math.pow',
                inputs=['base', 'exponent'],
                outputs=['first power']
            ),
            name='pow(2, 3)',
            spec={'base': 2, 'exponent': 3}
        )
        self.fw2 = Firework(
            PyTask(
                func='math.pow',
                inputs=['first power', 'exponent'],
                outputs=['second power']
            ),
            name='pow(pow(2, 3), 4)',
            spec={'exponent': 4}
        )
        self.fw3 = Firework(
            PyTask(
                func='print',
                inputs=['second power']
            ),
            name='the third one'
        )

    def test_dagflow_ok(self):
        """ construct and replicate """
        wfl = Workflow(
            [self.fw1, self.fw2, self.fw3],
            {self.fw1: [self.fw2], self.fw2: [self.fw3], self.fw3: []}
        )
        dagf = DAGFlow.from_fireworks(wfl)
        DAGFlow(**dagf.to_dict())

    def test_dagflow_loop(self):
        """ loop in graph """
        wfl = Workflow(
            [self.fw1, self.fw2, self.fw3],
            {self.fw1: self.fw2, self.fw2: self.fw3, self.fw3: self.fw1}
        )
        msg = 'The workflow graph must be a DAG.: found cycles:'
        with self.assertRaises(AssertionError) as context:
            DAGFlow.from_fireworks(wfl)
        self.assertTrue(msg in str(context.exception))

    def test_dagflow_cut(self):
        """ disconnected graph """
        wfl = Workflow([self.fw1, self.fw2, self.fw3], {self.fw1: self.fw2})
        msg = 'The workflow graph must be connected'
        with self.assertRaises(AssertionError) as context:
            DAGFlow.from_fireworks(wfl)
        self.assertTrue(msg in str(context.exception))

    def test_dagflow_link(self):
        """ wrong links """
        wfl = Workflow(
            [self.fw1, self.fw2, self.fw3],
            {self.fw1: [self.fw2, self.fw3]}
        )
        msg = 'An input field must have exactly one source'
        with self.assertRaises(AssertionError) as context:
            DAGFlow.from_fireworks(wfl)
        self.assertTrue(msg in str(context.exception))

    def test_dagflow_input(self):
        """ missing input """

        fw2 = Firework(
            PyTask(
                func='math.pow',
                inputs=['first power', 'exponent'],
                outputs=['second power']
            ),
            name='pow(pow(2, 3), 4)'
        )
        wfl = Workflow([self.fw1, fw2], {self.fw1: [fw2], fw2: []})
        msg = (r"An input field must have exactly one source', 'step', "
               r"'pow(pow(2, 3), 4)', 'entity', 'exponent', 'sources', []")
        with self.assertRaises(AssertionError) as context:
            DAGFlow.from_fireworks(wfl)
        self.assertTrue(msg in str(context.exception))

    def test_dagflow_output(self):
        """ clashing inputs """
        fw2 = Firework(
            PyTask(
                func='math.pow',
                inputs=['first power', 'exponent'],
                outputs=['second power']
            ),
            name='pow(pow(2, 3), 4)',
            spec={'exponent': 4, 'first power': 8}
        )
        wfl = Workflow([self.fw1, fw2], {self.fw1: [fw2], fw2: []})
        msg = (r"'An input field must have exactly one source', 'step', "
               r"'pow(pow(2, 3), 4)', 'entity', 'first power', 'sources'")
        with self.assertRaises(AssertionError) as context:
            DAGFlow.from_fireworks(wfl)
        self.assertTrue(msg in str(context.exception))

    def test_dagflow_view(self):
        """ visualize the workflow graph """
        wfl = Workflow(
            [self.fw1, self.fw2, self.fw3],
            {self.fw1: [self.fw2], self.fw2: [self.fw3], self.fw3: []}
        )
        dagf = DAGFlow.from_fireworks(wfl)
        dagf.add_step_labels()
        filename = str(uuid.uuid4())
        dagf.to_dot(filename, view='combined')
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)
        filename = str(uuid.uuid4())
        dagf.to_dot(filename, view='dataflow')
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)
        filename = str(uuid.uuid4())
        dagf.to_dot(filename, view='controlflow')
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)


if __name__ == '__main__':
    unittest.main()
