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

    def test_serialization(self):
        p = PBSAdapterNERSC()
        a = load_object(p.to_dict())
        print type(a)
        print PBSAdapterNERSC
        print isinstance(a, PBSAdapterNERSC)
        print isinstance(a, dict)
        self.assertIsInstance(a, PBSAdapterNERSC)


if __name__ == '__main__':
    unittest.main()
