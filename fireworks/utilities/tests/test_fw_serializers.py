#!/usr/bin/env python

'''
TODO: add docs
'''
from fireworks.utilities.tests.test_serializer import TestSerializer


__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 26, 2013"

import unittest
import datetime

# TODO: unicode TEST
# TODO: add file import/export test
# TODO: add implicit and one-line serialization tests


class SerializationTest(unittest.TestCase):

    def setUp(self):
        test_date = datetime.datetime.utcnow()
        self.obj_1 = TestSerializer("prop1", test_date)
        self.obj_1_copy = TestSerializer("prop1", test_date)
        self.obj_2 = TestSerializer({"p1": 1234, "p2": 5.0, "p3": "Hi!", 'p4': datetime.datetime.utcnow()}, test_date)
        
    def test_sanity(self):
        self.assertEqual(self.obj_1, self.obj_1_copy, "The __eq__() method of the TestSerializer is not set up properly!")
        self.assertNotEqual(self.obj_1, self.obj_2, "The __ne__() method of the TestSerializer is not set up properly!")
        self.assertEqual(self.obj_1, self.obj_1.from_dict(self.obj_1.to_dict()), "The to/from_dict() methods of the TestSerializer are not set up properly!")
    
    def test_serialize_fw_decorator(self):
        m_dict = self.obj_1.to_dict()
        self.assertEqual(m_dict['_fw_name'], 'TestSerializer Name')
        self.assertEqual(m_dict['@class'], 'TestSerializer')
        self.assertEqual(m_dict['@module'], 'fireworks.utilities.tests.test_serializer')
        
    def test_json(self):
        obj1_json_string = str(self.obj_1.to_format())  # default format is JSON, make sure this is true
        self.assertEqual(self.obj_1.from_format(obj1_json_string), self.obj_1, 'JSON format export / import fails!')

    def test_yaml(self):
        obj1_yaml_string = str(self.obj_1.to_format('yaml'))
        self.assertEqual(self.obj_1.from_format(obj1_yaml_string, 'yaml'), self.obj_1, 'YAML format export / import fails!')
    
    def test_complex_json(self):
        obj2_json_string = str(self.obj_2.to_format())  # default format is JSON, make sure this is true
        self.assertEqual(self.obj_2.from_format(obj2_json_string), self.obj_2, 'Complex JSON format export / import fails!')
    
    def test_complex_yaml(self):
        obj2_yaml_string = str(self.obj_2.to_format('yaml'))
        self.assertEqual(self.obj_2.from_format(obj2_yaml_string, 'yaml'), self.obj_2, 'Complex YAML format export / import fails!')
                
if __name__ == "__main__":
    unittest.main()