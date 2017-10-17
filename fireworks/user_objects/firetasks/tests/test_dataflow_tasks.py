""" Unit tests for the dataflow tasks """

__author__ = 'Ivan Kondov'
__copyright__ = 'Copyright 2017, Karlsruhe Institute of Technology'
__email__ = 'ivan.kondov@kit.edu'

import os
import unittest

from fireworks.user_objects.firetasks.dataflow_tasks import CommandLineTask
from fireworks.user_objects.firetasks.dataflow_tasks import ForeachTask
from fireworks.user_objects.firetasks.dataflow_tasks import JoinDictTask
from fireworks.user_objects.firetasks.dataflow_tasks import JoinListTask
from fireworks.user_objects.firetasks.dataflow_tasks import ImportDataTask

class CommandLineTaskTest(unittest.TestCase):

    def test_command_line_task_1(self):
        """
        input from string to stdin and output from stdout to string
        """
        params = {
            'command_spec': {
                'command': ['cat'],
                'input string': {
                    'source': 'hello input',
                    'target': {'type': 'stdin'}
                },
                'output string': {
                    'source': {'type': 'stdout'},
                    'target': {'type': 'data'}
                }
            },
            'inputs': ['input string'],
            'outputs': ['output string']
        }
        spec = {'hello input': {'type': 'data', 'value': 'Hello world!'}}
        firetask = CommandLineTask(**params)
        action = firetask.run_task(spec)
        output_string = action.update_spec['output string']['value']
        self.assertEqual(output_string, 'Hello world!')

    def test_command_line_task_2(self):
        """
        input from string to data and output from stdout to file
        input from file to stdin and output from stdout to string
        """
        params = {
            'command_spec': {
                'command': ['echo'],
                'input string': {'source': 'input string'},
                'output file': {
                    'source': {'type': 'stdout'},
                    'target': {'type': 'path', 'value': '/tmp'}
                }
            },
            'inputs': ['input string'],
            'outputs': ['output file']
        }
        spec = {'input string': {'type': 'data', 'value': 'Hello world!'}}
        firetask = CommandLineTask(**params)
        action = firetask.run_task(spec)
        filename = action.update_spec['output file']['value']
        self.assertTrue(os.path.exists(filename))
        with open(filename) as fp:
            line = fp.readlines()[0]
            self.assertTrue('Hello world!' in line)

        params = {
            'command_spec': {
                'command': ['cat'],
                'output string': {
                    'source': {'type': 'stdout'},
                    'target': {'type': 'data'}
                },
                'input file': {
                    'target': {'type': 'stdin'},
                    'source': 'input file'
                }
            },
            'inputs': ['input file'],
            'outputs': ['output string']
        }
        spec = {'input file':  {'type': 'path', 'value': filename}}
        firetask = CommandLineTask(**params)
        action = firetask.run_task(spec)
        output_string = action.update_spec['output string']['value']
        self.assertEqual(output_string, 'Hello world!')
        os.remove(filename)


class ForeachTaskTest(unittest.TestCase):
    pass


class JoinDictTaskTest(unittest.TestCase):
    pass


class JoinListTaskTest(unittest.TestCase):
    pass


class ImportDataTaskTest(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
