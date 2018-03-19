""" Unit tests for the dataflow tasks """
from unittest import SkipTest

__author__ = 'Ivan Kondov'
__copyright__ = 'Copyright 2017, Karlsruhe Institute of Technology'
__email__ = 'ivan.kondov@kit.edu'

import os
import unittest
import uuid

from fireworks.user_objects.firetasks.dataflow_tasks import CommandLineTask
from fireworks.user_objects.firetasks.dataflow_tasks import ForeachTask
from fireworks.user_objects.firetasks.dataflow_tasks import JoinDictTask
from fireworks.user_objects.firetasks.dataflow_tasks import JoinListTask
from fireworks.user_objects.firetasks.dataflow_tasks import ImportDataTask

def afunc(array, power):
    """ return the powers of a list of numbers """
    return [pow(number, power) for number in array]

class CommandLineTaskTest(unittest.TestCase):
    """ run tests for CimmandLineTask """

    def test_command_line_task_1(self):
        """ input from string to stdin, output from stdout to string """
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
        action = CommandLineTask(**params).run_task(spec)
        output_string = action.update_spec['output string']['value']
        self.assertEqual(output_string, 'Hello world!')

        params['chunk_number'] = 0
        action = CommandLineTask(**params).run_task(spec)
        output_string = action.mod_spec[0]['_push']['output string']['value']
        self.assertEqual(output_string, 'Hello world!')

    def test_command_line_task_2(self):
        """
        input from string to data, output from stdout to file;
        input from file to stdin, output from stdout to string and from file
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
        action = CommandLineTask(**params).run_task(spec)
        filename = action.update_spec['output file']['value']
        self.assertTrue(os.path.exists(filename))
        with open(filename, 'r') as fptr:
            self.assertEqual(fptr.read().strip(), 'Hello world!')

        params = {
            'command_spec': {
                'command': ['tee'],
                'output string': {
                    'source': {'type': 'stdout'},
                    'target': {'type': 'data'}
                },
                'input file': {
                    'target': {'type': 'stdin'},
                    'source': 'input file'
                },
                'output file': {
                    'source': 'tee file',
                    'target': {'type': 'path', 'value': '.'}
                }
            },
            'inputs': ['input file'],
            'outputs': ['output string', 'output file']
        }
        spec = {
            'input file':  {'type': 'path', 'value': filename},
            'tee file':  {'type': 'data', 'value': str(uuid.uuid4())},
        }
        action = CommandLineTask(**params).run_task(spec)
        output_string = action.update_spec['output string']['value']
        self.assertEqual(output_string, 'Hello world!')
        output_file = action.update_spec['output file']['value']
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r') as fptr:
            self.assertEqual(fptr.read().strip(), 'Hello world!')
        os.remove(filename)
        os.remove(output_file)

    def test_command_line_task_3(self):    
        """ input from string to data with command line options """
        import platform
        if platform.system() != 'Linux':
            raise SkipTest("Command line test skipped for non-Linux platform")
        spec = {}
        params = {
            'command_spec': {
                'command': ['date'],
                'date option': {
                    'binding': {'prefix': '--iso', 'separator': '='},
                    'source': {'type': 'data', 'value': 'second'}
                },
                'input string': {'source': 'input string'},
                'time stamp': {
                    'source': {'type': 'stdout'},
                    'target': {'type': 'data'}
                }
            },
            'inputs': ['date option'],
            'outputs': ['time stamp']
        }
        action = CommandLineTask(**params).run_task(spec)

        spec.update(action.update_spec)
        time_stamp_1 = action.update_spec['time stamp']['value']
        filename = str(uuid.uuid4())
        spec['file name'] = {'type': 'data', 'value': filename}
        params = {
            'command_spec': {
                'command': ['touch'],
                'filename': {
                    'source': 'file name'
                },
                'time stamp': {
                    'binding': {'prefix': '--date', 'separator': '='},
                    'source': 'time stamp',
                }
            },
            'inputs': ['time stamp', 'filename'],
            'outputs': []
        }
        action = CommandLineTask(**params).run_task(spec)
        self.assertTrue(os.path.exists(spec['file name']['value']))

        spec = {}
        params = {
            'command_spec': {
                'command': ['stat'],
                'filename': {
                    'source': {'type': 'data', 'value': filename}
                },
                'format option': {
                    'binding': {'prefix': '-c', 'separator': ' '},
                    'source': {'type': 'data', 'value': '%y'}
                },
                'date and time': {
                    'source': {'type': 'stdout'},
                    'target': {'type': 'data'}
                }
            },
            'inputs': ['format option', 'filename'],
            'outputs': ['date and time']
        }
        action = CommandLineTask(**params).run_task(spec)
        time_stamp_2 = action.update_spec['date and time']['value']
        self.assertEqual(time_stamp_1[0:10], time_stamp_2[0:10])
        self.assertEqual(time_stamp_1[11:19], time_stamp_2[11:19])
        os.remove(filename)

    def test_command_line_task_4(self):
        """ multiple string inputs, multiple file outputs """
        params = {
            'command_spec': {
                'command': ['touch'],
                'filename_1': {
                    'source': 'f_name_1'
                },
                'filename_2': {
                    'source': 'f_name_2'
                },
                'file_1': {
                    'source': 'f_name_1',
                    'target': {'type': 'path', 'value': '.'}
                },
                'file_2': {
                    'source': 'f_name_2',
                    'target': {'type': 'path', 'value': '.'}
                }
            },
            'inputs': ['filename_1', 'filename_2'],
            'outputs': ['file_1', 'file_2']
        }
        spec = {
            'f_name_1': {'type': 'data', 'value': str(uuid.uuid4())},
            'f_name_2': {'type': 'path', 'value': str(uuid.uuid4())}
        }
        action = CommandLineTask(**params).run_task(spec)
        o_file_1 = action.update_spec['file_1']['value']
        o_file_2 = action.update_spec['file_2']['value']
        self.assertTrue(os.path.exists(o_file_1))
        self.assertTrue(os.path.exists(o_file_2))
        self.assertTrue(os.path.exists(spec['f_name_1']['value']))
        self.assertTrue(os.path.exists(spec['f_name_2']['value']))
        os.remove(o_file_1)
        os.remove(o_file_2)
        os.remove(spec['f_name_1']['value'])
        os.remove(spec['f_name_2']['value'])


class ForeachTaskTest(unittest.TestCase):
    """ run tests for ForeachTask """

    def test_foreach_pytask(self):
        """ run PyTask for a list of numbers """
        numbers = [0, 1, 2, 3, 4]
        power = 2
        spec = {'numbers': numbers, 'power': power}
        task = {
            '_fw_name': 'PyTask',
            'func': afunc.__module__ + '.' + afunc.__name__,
            'inputs': ['numbers', 'power'],
            'outputs': ['results']
        }
        params = {'task': task, 'split': 'numbers', 'number of chunks': 3}
        action = ForeachTask(**params).run_task(spec)
        results = []
        for detour in action.detours:
            action = detour.tasks[0].run_task(detour.spec)
            for mod in action.mod_spec:
                results.append(mod['_push']['results'])
        for (number, result) in zip(numbers, results):
            self.assertEqual(result, pow(number, power))

    def test_foreach_commandlinetask(self):
        """ run CommandLineTask for a list of input data """
        inputs = ['black', 'white', 2.5, 17]
        worklist = [{'source': {'type': 'data', 'value': s}} for s in inputs]
        spec = {'work list': worklist}
        task = {
            '_fw_name': 'CommandLineTask',
            'command_spec': {
                'command': ['echo'],
                'file set': {
                    'source': {'type': 'stdout'},
                    'target': {'type': 'path', 'value': '.'}
                },
                'work list': 'work list'
            },
            'inputs': ['work list'],
            'outputs': ['file set']
        }
        params = {'task': task, 'split': 'work list', 'number of chunks': 2}
        action = ForeachTask(**params).run_task(spec)
        outputs = []
        for detour in action.detours:
            action = detour.tasks[0].run_task(detour.spec)
            ofile = action.mod_spec[0]['_push']['file set']['value']
            self.assertTrue(os.path.exists(ofile))
            with open(ofile, 'r') as fptr:
                outputs.append(fptr.read().strip())
            os.remove(ofile)
        ref_str = ' '.join(str(inp) for inp in inputs)
        out_str = ' '.join(str(out) for out in outputs)
        self.assertEqual(out_str, ref_str)


class JoinDictTaskTest(unittest.TestCase):
    """ run tests for JoinDictTask """

    def test_join_dict_task(self):
        """ joins dictionaries into a new or existing dict in spec """
        temperature = {'value': 273.15, 'units': 'Kelvin'}
        pressure = {'value': 1.2, 'units': 'bar'}
        spec = {
            'temperature': temperature,
            'pressure': pressure
        }
        params = {
            'inputs': ['temperature', 'pressure'],
            'output': 'state parameters'
        }

        action = JoinDictTask(**params).run_task(spec)
        odict = action.update_spec['state parameters']
        self.assertTrue('temperature' in odict)
        self.assertTrue('pressure' in odict)
        self.assertEqual(odict['pressure']['value'], pressure['value'])

        spec['state parameters'] = {'potential': {}}
        params['rename'] = {'temperature': 'temp', 'pressure': 'pres'}
        action = JoinDictTask(**params).run_task(spec)
        odict = action.update_spec['state parameters']
        self.assertTrue('temp' in odict)
        self.assertTrue('pres' in odict)
        self.assertTrue('potential' in odict)
        self.assertEqual(odict['pres']['value'], pressure['value'])


class JoinListTaskTest(unittest.TestCase):
    """ run tests for JoinListTask """

    def test_join_list_task(self):
        """ joins items into a new or existing list in spec """
        temperature = {'value': 273.15, 'units': 'Kelvin'}
        pressure = {'value': 1.2, 'units': 'bar'}
        spec = {
            'temperature': temperature,
            'pressure': pressure
        }
        params = {
            'inputs': ['temperature', 'pressure'],
            'output': 'state parameters'
        }

        action = JoinListTask(**params).run_task(spec)
        olist = action.update_spec['state parameters']
        self.assertEqual(olist[0]['units'], temperature['units'])
        self.assertEqual(olist[1]['value'], pressure['value'])

        spec['state parameters'] = [{}]
        action = JoinListTask(**params).run_task(spec)
        olist = action.update_spec['state parameters']
        self.assertEqual(olist[0], {})
        self.assertEqual(olist[1]['units'], temperature['units'])
        self.assertEqual(olist[2]['value'], pressure['value'])


class ImportDataTaskTest(unittest.TestCase):
    """ run tests for ImportDataTask """

    def test_import_data_task(self):
        """ loads data from a file into spec """
        import json
        import ruamel.yaml as yaml
        temperature = {'value': 273.15, 'units': 'Kelvin'}
        spec = {'state parameters': {}}
        formats = {'json': json, 'yaml': yaml}
        params = {'mapstring': 'state parameters/temperature'}
        for fmt in formats:
            filename = str(uuid.uuid4()) + '.' + fmt
            params['filename'] = filename
            with open(filename, 'w') as fptr:
                formats[fmt].dump(temperature, fptr)
            action = ImportDataTask(**params).run_task(spec)
            root = action.update_spec['state parameters']
            self.assertTrue('temperature' in root)
            self.assertTrue('value' in root['temperature'])
            self.assertEqual(root['temperature']['units'], temperature['units'])
            os.remove(filename)


if __name__ == '__main__':
    unittest.main()
