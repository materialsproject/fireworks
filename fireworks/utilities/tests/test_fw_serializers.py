# coding: utf-8

#from __future__ import unicode_literals

import sys
from fireworks.user_objects.firetasks.unittest_tasks import TestSerializer, ExportTestSerializer
from fireworks.utilities.fw_serializers import load_object, FWSerializable
from fireworks.utilities.fw_utilities import explicit_serialize


__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 26, 2013"

import unittest
import datetime
import os
import json


if sys.version_info > (3, 0, 0):
    ENCODING_PARAMS = {"encoding": "utf-8"}
else:
    ENCODING_PARAMS = {}


@explicit_serialize
class ExplicitTestSerializer(FWSerializable):
    def __init__(self, a):
        self.a = a

    def __eq__(self, other):
        return self.a == other.a

    def to_dict(self):
        return {"_fw_name": self.fw_name, "a": self.a}

    @classmethod
    def from_dict(cls, m_dict):
        return ExplicitTestSerializer(m_dict["a"])


class SerializationTest(unittest.TestCase):
    def setUp(self):
        test_date = datetime.datetime.utcnow()
        # A basic datetime test serialized object
        self.obj_1 = TestSerializer("prop1", test_date)
        self.obj_1_copy = TestSerializer("prop1", test_date)

        # A nested test serialized object
        self.obj_2 = TestSerializer({"p1": 1234, "p2": 5.0, "p3": "Hi!", 'p4': datetime.datetime.utcnow()}, test_date)

        # A unicode test serialized object
        unicode_str = u'\xe4\xf6\xfc'
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
        with open(os.path.join(self.module_dir, "test_reference.json")) as f,\
                open("test.json", **ENCODING_PARAMS) as f2:
            obj1 = json.load(f)
            obj2 = json.load(f2)
            self.assertEqual(obj1, obj2, 'Unicode JSON file export fails')

        self.assertEqual(self.obj_3.from_file("test.json"), self.obj_3, 'Unicode JSON file import fails!')

    def test_unicode_yaml_file(self):
        with open(os.path.join(self.module_dir, "test_reference.yaml"),
                  **ENCODING_PARAMS) as f:
            with open("test.yaml", **ENCODING_PARAMS) as f2:
                self.assertEqual(f.read(), f2.read(), 'Unicode JSON file export fails')

        self.assertEqual(self.obj_3.from_file("test.yaml"), self.obj_3, 'Unicode YAML file import fails!')

    def test_implicit_serialization(self):
        self.assertEqual(load_object({"a": {"p1": {"p2": 3}}, "_fw_name": "TestSerializer Export Name"}), self.obj_4,
                         'Implicit import fails!')

    def test_as_dict(self):
        self.assertEqual(self.obj_1.as_dict(), self.obj_1.to_dict())


class ExplicitSerializationTest(unittest.TestCase):
    def setUp(self):
        self.s_obj = ExplicitTestSerializer(1)
        self.s_dict = self.s_obj.to_dict()

    def test_explicit_serialization(self):
        self.assertEqual(load_object(self.s_dict), self.s_obj)

if __name__ == "__main__":
    unittest.main()
