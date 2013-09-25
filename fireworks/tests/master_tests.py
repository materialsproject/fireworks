#!/usr/bin/env python

"""
Master tests for FireWorks - generally used to ensure that installation was \
completed properly.
"""

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 9, 2013"

import unittest


class TestImports(unittest.TestCase):
    """
    Make sure that required external libraries can be imported 
    """

    def test_imports(self):
        import yaml
        import pymongo
        import jinja2
        # test that MongoClient is available (newer pymongo)
        from pymongo import MongoClient


if __name__ == "__main__":
    unittest.main()