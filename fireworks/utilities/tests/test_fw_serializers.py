#!/usr/bin/env python

'''
TODO: add docs
'''
from fireworks.utilities.fw_serializers import FWSerializable, serialize_fw


__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 26, 2013"

import unittest
import datetime

# TODO: wrong module name....
# TODO: test class name, fw_name, module name

class SerializationTest(unittest.TestCase):

    def setUp(self):
        
        class TestSerializer(FWSerializable):
            _fw_name = 'TestSerializer'
            
            def __init__(self, a, m_date):
                if not isinstance(m_date, datetime.datetime):
                    raise ValueError("m_date must be a datetime instance!")
                
                self.a = a
                self.m_date = m_date
            
            def __eq__(self, other):
                return self.a == other.a and self.m_date == other.m_date
            
            @serialize_fw
            def to_dict(self):
                return {"a": self.a, "m_date": self.m_date}
            
            @classmethod
            def from_dict(self, m_dict):
                return TestSerializer(m_dict["a"], m_dict["m_date"])

        test_date = datetime.datetime.utcnow()
        self.obj_1 = TestSerializer("prop1", test_date)
        self.obj_1_copy = TestSerializer("prop1", test_date)
        self.obj_2 = TestSerializer("prop2", test_date)
        
    def test_sanity(self):
        self.assertEqual(self.obj_1, self.obj_1_copy, "The __eq__() method of the TestSerializer is not set up properly!")
        self.assertNotEqual(self.obj_1, self.obj_2, "The __ne__() method of the TestSerializer is not set up properly!")
        self.assertEqual(self.obj_1, self.obj_1.from_dict(self.obj_1.to_dict()), "The to/from_dict() methods of the TestSerializer are not set up properly!")
    
    def test_json(self):
        obj1_json_string = str(self.obj_1.to_format())  # default format is JSON, make sure this is true
        self.assertEqual(self.obj_1.from_format(obj1_json_string), self.obj_1, 'JSON format export / import fails!')

    def test_yaml(self):
        obj1_yaml_string = str(self.obj_1.to_format('yaml'))
        self.assertEqual(self.obj_1.from_format(obj1_yaml_string, 'yaml'), self.obj_1, 'YAML format export / import fails!')
        
if __name__ == "__main__":
    unittest.main()