""" TODO: Modify unittest doc. """
# coding: utf-8

from __future__ import unicode_literals, division
import unittest
import os
from fireworks.user_objects.firetasks.script_task import ScriptTask, PyTask

__author__ = "Shyue Ping Ong, Bharat Medasani"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__date__ = "2/16/14"


def afunc(y, z, a):
    return [pow(x, y, z) for x in a]

class ScriptTaskTest(unittest.TestCase):

    def test_scripttask(self):
        if os.path.exists('hello.txt'):
            os.remove('hello.txt')
        s = ScriptTask({'script': 'echo "hello world"',
                        'stdout_file': 'hello.txt'})
        s.run_task({})
        self.assertTrue(os.path.exists('hello.txt'))
        with open('hello.txt') as fp:
            line = fp.readlines()[0]
            self.assertTrue('hello world' in line)
        os.remove('hello.txt')


class PyTaskTest(unittest.TestCase):

    def test_task(self):
        p = PyTask(func='json.dumps', kwargs={'obj': {'hello': 'world'}},
                   stored_data_varname='json')
        a = p.run_task({})
        self.assertEqual(a.stored_data['json'], '{"hello": "world"}')
        p = PyTask(func='pow', args=[3, 2], stored_data_varname='data')
        a = p.run_task({})
        self.assertEqual(a.stored_data['data'], 9)
        p = PyTask(func='print', args=[3])
        p.run_task({})

    def test_task_auto_kwargs(self):
        p = PyTask(func='json.dumps', obj={'hello': 'world'},
                   stored_data_varname="json", auto_kwargs=True)
        a = p.run_task({})
        self.assertEqual(a.stored_data['json'], '{"hello": "world"}')
        p = PyTask(func='pow', args=[3, 2], stored_data_varname='data')
        a = p.run_task({})
        self.assertEqual(a.stored_data['data'], 9)
        p = PyTask(func='print', args=[3])
        p.run_task({})

    def test_task_data_flow(self):
        """ test dataflow parameters: inputs, outputs and chunk_number """
        params = {'func': 'pow', 'inputs': ['arg', 'power', 'modulo'],
                  'stored_data_varname': 'data'}
        spec = {'arg': 2, 'power': 3, 'modulo': None}
        action = PyTask(**params).run_task(spec)
        self.assertEqual(action.stored_data['data'], 8)

        params['outputs'] = ['result']
        action = PyTask(**params).run_task(spec)
        self.assertEqual(action.stored_data['data'], 8)
        self.assertEqual(action.update_spec['result'], 8)

        params['chunk_number'] = 0
        action = PyTask(**params).run_task(spec)
        self.assertEqual(action.stored_data['data'], 8)
        self.assertEqual(action.mod_spec[0]['_push']['result'], 8)

        params['args'] = [2, 3]
        params['inputs'] = ['modulo']
        spec = {'modulo': 3}
        action = PyTask(**params).run_task(spec)
        self.assertEqual(action.stored_data['data'], 2)
        self.assertEqual(action.mod_spec[0]['_push']['result'], 2)

        params['func'] = afunc.__module__ + '.' + afunc.__name__
        params['args'] = [3, 3]
        params['inputs'] = ['array']
        spec = {'array': [1, 2]}
        action = PyTask(**params).run_task(spec)
        self.assertEqual(action.stored_data['data'], [1, 2])
        self.assertEqual(action.mod_spec[0]['_push']['result'], 1)
        self.assertEqual(action.mod_spec[1]['_push']['result'], 2)

        del params['chunk_number']
        action = PyTask(**params).run_task(spec)
        self.assertEqual(action.update_spec['result'][0], 1)
        self.assertEqual(action.update_spec['result'][1], 2)

        params['outputs'] = ['first', 'second']
        action = PyTask(**params).run_task(spec)
        self.assertEqual(action.update_spec['first'], 1)
        self.assertEqual(action.update_spec['second'], 2)


if __name__ == '__main__':
    unittest.main()
