# coding: utf-8

from __future__ import unicode_literals, division

"""
TODO: Modify unittest doc.
"""


__author__ = "Shyue Ping Ong, Bharat Medasani"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__date__ = "2/16/14"

import unittest
import os

from fireworks.user_objects.firetasks.script_task import ScriptTask, PyTask

class ScriptTaskTest(unittest.TestCase):

    def test_scripttask(self):
        if os.path.exists('hello.txt'):
            os.remove('hello.txt')
        s = ScriptTask({'script':"echo 'hello world'",'stdout_file':'hello.txt'})
        s.run_task({})
        self.assertTrue(os.path.exists('hello.txt'))
        with open('hello.txt') as fp:
            line = fp.readlines()[0]
            self.assertTrue('hello world' in line)
        os.remove('hello.txt')


class PyTaskTest(unittest.TestCase):

    def test_task(self):
        p = PyTask(func="json.dumps", kwargs={"obj":{"hello": "world"}},
                       stored_data_varname="json")
        a = p.run_task({})
        self.assertEqual(a.stored_data["json"], '{"hello": "world"}')
        p = PyTask(func="pow", args=[3, 2], stored_data_varname="data")
        a = p.run_task({})
        self.assertEqual(a.stored_data["data"], 9)
        p = PyTask(func="print", args=[3])
        p.run_task({})

    def test_task_auto_kwargs(self):
        p = PyTask(func="json.dumps", obj={"hello": "world"},
                       stored_data_varname="json", auto_kwargs=True)
        a = p.run_task({})
        self.assertEqual(a.stored_data["json"], '{"hello": "world"}')
        p = PyTask(func="pow", args=[3, 2], stored_data_varname="data")
        a = p.run_task({})
        self.assertEqual(a.stored_data["data"], 9)
        p = PyTask(func="print", args=[3])
        p.run_task({})


if __name__ == '__main__':
    unittest.main()
