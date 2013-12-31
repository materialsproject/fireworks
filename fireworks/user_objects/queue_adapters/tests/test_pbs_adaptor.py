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
__date__ = "12/31/13"

import unittest

from fireworks.user_objects.queue_adapters.pbs_adapter import *
from fireworks.utilities.fw_serializers import load_object

class PBSAdaptorTest(unittest.TestCase):

    # def test_serialization(self):
    #     p = PBSAdapterNERSC()
    #     a = load_object(p.to_dict())
    #     print type(a)
    #     print PBSAdapterNERSC
    #     print isinstance(a, PBSAdapterNERSC)
    #     print isinstance(a, dict)
    #     self.assertIsInstance(a, PBSAdapterNERSC)

    def test_serialization(self):
        p = PBSAdapter(
            q_name="hello",
            template_file=os.path.join(os.path.dirname(__file__),
                                       "mypbs.txt"),
                       hello="world", queue="random")
        p_new = load_object(p.to_dict())

        #Make sure the original and deserialized verison both work properly.
        for a in [p, p_new]:
            script = a.get_script_str("here")
            lines = script.split("\n")
            self.assertIn("# world", lines)
            self.assertIn("#PBS -q random", lines)

        p = PBSAdapter(
            q_name="hello",
            hello="world", queue="random")
        #this uses the default template, which does not have $${hello}
        self.assertNotEqual("# world", p.get_script_str("here").split("\n")[
            -1])
        self.assertIsNone(p.to_dict()["_fw_template_file"])


if __name__ == '__main__':
    unittest.main()
