#!/usr/bin/env python

"""
TODO: add docs
"""
from fireworks.utilities.fw_serializers import load_object
from fireworks.utilities.tests.test_serializer import TestSerializer, \
    ExportTestSerializer


__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 26, 2013"

import unittest
import datetime
import os


class SerializationTest(unittest.TestCase):
    def setUp(self):
        test_date = datetime.datetime.utcnow()
        # A basic datetime test serialized object
        self.obj_1 = TestSerializer("prop1", test_date)
        self.obj_1_copy = TestSerializer("prop1", test_date)

        # A nested test serialized object
        self.obj_2 = TestSerializer({"p1": 1234, "p2": 5.0, "p3": "Hi!", 'p4': datetime.datetime.utcnow()}, test_date)

        # A unicode test serialized object
        unicode_str = unicode('\xc3\xa4\xc3\xb6\xc3\xbc', 'utf-8')
        self.obj_3 = ExportTestSerializer({"p1": unicode_str, "p2": "abc"})
        self.obj_3.to_file("test.json")
        self.obj_3.to_file("test.yaml")

        # A simpler test serialized object for testing implicit serialization
        self.obj_4 = ExportTestSerializer({"p1": {"p2": 3}})

        self.module_dir = os.path.dirname(os.path.abspath(__file__))

    def tearDown(self):
        os.remove("test.json")
        os.remove('test.yaml')

    def test_sanity(self):
        self.assertEqual(self.obj_1, self.obj_1_copy,
                         "The __eq__() method of the TestSerializer is not set up properly!")
        self.assertNotEqual(self.obj_1, self.obj_2, "The __ne__() method of the TestSerializer is not set up properly!")
        self.assertEqual(self.obj_1, self.obj_1.from_dict(self.obj_1.to_dict()),
                         "The to/from_dict() methods of the TestSerializer are not set up properly!")

    def test_serialize_fw_decorator(self):
        m_dict = self.obj_1.to_dict()
        self.assertEqual(m_dict['_fw_name'], 'TestSerializer Name')

    def test_json(self):
        obj1_json_string = str(self.obj_1.to_format())  # default format is JSON, make sure this is true
        self.assertEqual(self.obj_1.from_format(obj1_json_string), self.obj_1, 'JSON format export / import fails!')

    def test_yaml(self):
        obj1_yaml_string = str(self.obj_1.to_format('yaml'))
        self.assertEqual(self.obj_1.from_format(obj1_yaml_string, 'yaml'), self.obj_1,
                         'YAML format export / import fails!')

    def test_complex_json(self):
        obj2_json_string = str(self.obj_2.to_format())  # default format is JSON, make sure this is true
        self.assertEqual(self.obj_2.from_format(obj2_json_string), self.obj_2,
                         'Complex JSON format export / import fails!')

    def test_complex_yaml(self):
        obj2_yaml_string = str(self.obj_2.to_format('yaml'))
        self.assertEqual(self.obj_2.from_format(obj2_yaml_string, 'yaml'), self.obj_2,
                         'Complex YAML format export / import fails!')

    def test_unicode_json(self):
        obj3_json_string = str(self.obj_3.to_format())  # default format is JSON, make sure this is true
        self.assertEqual(self.obj_3.from_format(obj3_json_string), self.obj_3,
                         'Unicode JSON format export / import fails!')

    def test_unicode_yaml(self):
        obj3_yaml_string = str(self.obj_3.to_format('yaml'))
        self.assertEqual(self.obj_3.from_format(obj3_yaml_string, 'yaml'), self.obj_3,
                         'Unicode YAML format export / import fails!')

    def test_unicode_json_file(self):
        with open(os.path.join(self.module_dir, "test_reference.json")) as f:
            with open("test.json") as f2:
                self.assertEqual(f.read(), f2.read(), 'Unicode JSON file export fails')

        self.assertEqual(self.obj_3.from_file("test.json"), self.obj_3, 'Unicode JSON file import fails!')

    def test_unicode_yaml_file(self):
        with open(os.path.join(self.module_dir, "test_reference.yaml")) as f:
            with open("test.yaml") as f2:
                self.assertEqual(f.read(), f2.read(), 'Unicode JSON file export fails')

        self.assertEqual(self.obj_3.from_file("test.yaml"), self.obj_3, 'Unicode YAML file import fails!')

    def test_implicit_serialization(self):
        self.assertEqual(load_object({"a": {"p1": {"p2": 3}}, "_fw_name": "TestSerializer Export Name"}), self.obj_4,
                         'Implicit import fails!')


if __name__ == "__main__":
    unittest.main()