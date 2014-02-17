#!/usr/bin/env python

"""
TODO: Modify unittest doc.
"""

from __future__ import division

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__date__ = "2/16/14"

import unittest

from fireworks.user_objects.firetasks.script_task import PyTask

class PythonTaskTest(unittest.TestCase):

    def test_task(self):
        p = PyTask(func="json.dumps", obj={"hello": "world"},
                       stored_data_varname="json")
        a = p.run_task({})
        self.assertEqual(a.stored_data["json"], '{"hello": "world"}')
        p = PyTask(func="pow", args=[3, 2], stored_data_varname="data")
        a = p.run_task({})
        self.assertEqual(a.stored_data["data"], 9)
        p = PyTask(func="print", args=[3])
        a = p.run_task({})


if __name__ == '__main__':
    unittest.main()
