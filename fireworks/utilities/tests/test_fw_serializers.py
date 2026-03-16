from __future__ import annotations

import datetime
import json
import os
import unittest
from tempfile import mkdtemp
from typing import Any

import numpy as np
import pytest

from fireworks.user_objects.firetasks.unittest_tasks import ExportTestSerializer, UnitTestSerializer
from fireworks.utilities.exceptions import FWFormatError, FWSerializationError
from fireworks.utilities.fw_serializers import FWSerializable, load_object, load_object_from_file, recursive_dict
from fireworks.utilities.fw_utilities import explicit_serialize

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 26, 2013"

ENCODING_PARAMS = {"encoding": "utf-8"}


@explicit_serialize
class ExplicitTestSerializer(FWSerializable):
    def __init__(self, a) -> None:
        self.a = a

    def __eq__(self, other: object) -> bool:
        """Check equality with another object."""
        return self.a == getattr(other, "a", None)

    def __hash__(self) -> int:
        """Return hash of the object."""
        return hash(self.a)

    def to_dict(self) -> dict[str, Any]:
        return {"_fw_name": self.fw_name, "a": self.a}

    @classmethod
    def from_dict(cls, m_dict):
        return ExplicitTestSerializer(m_dict["a"])


class SerializationTest(unittest.TestCase):
    def setUp(self) -> None:
        test_date = datetime.datetime.now(datetime.timezone.utc)
        # A basic datetime test serialized object
        self.obj_1 = UnitTestSerializer("prop1", test_date)
        self.obj_1_copy = UnitTestSerializer("prop1", test_date)

        # A nested test serialized object
        self.obj_2 = UnitTestSerializer(
            {"p1": 1234, "p2": 5.0, "p3": "Hi!", "p4": datetime.datetime.now(datetime.timezone.utc)}, test_date
        )

        # A unicode test serialized object
        unicode_str = "\xe4\xf6\xfc"
        self.obj_3 = ExportTestSerializer({"p1": unicode_str, "p2": "abc"})
        self.obj_3.to_file("test.json")
        self.obj_3.to_file("test.yaml")

        # A simpler test serialized object for testing implicit serialization
        self.obj_4 = ExportTestSerializer({"p1": {"p2": 3}})

        self.module_dir = os.path.dirname(os.path.abspath(__file__))

    def tearDown(self) -> None:
        os.remove("test.json")
        os.remove("test.yaml")

    def test_sanity(self) -> None:
        assert self.obj_1 == self.obj_1_copy, "The __eq__() method of the TestSerializer is not set up properly!"
        assert self.obj_1 != self.obj_2, "The __ne__() method of the TestSerializer is not set up properly!"
        assert self.obj_1 == self.obj_1.from_dict(self.obj_1.to_dict()), (
            "The to/from_dict() methods of the TestSerializer are not set up properly!"
        )

    def test_serialize_fw_decorator(self) -> None:
        m_dict = self.obj_1.to_dict()
        assert m_dict["_fw_name"] == "TestSerializer Name"

    def test_json(self) -> None:
        obj1_json_string = str(self.obj_1.to_format())  # default format is JSON, make sure this is true
        assert self.obj_1.from_format(obj1_json_string) == self.obj_1, "JSON format export / import fails!"

    def test_yaml(self) -> None:
        obj1_yaml_string = str(self.obj_1.to_format("yaml"))
        assert self.obj_1.from_format(obj1_yaml_string, "yaml") == self.obj_1, "YAML format export / import fails!"

    def test_complex_json(self) -> None:
        obj2_json_string = str(self.obj_2.to_format())  # default format is JSON, make sure this is true
        assert self.obj_2.from_format(obj2_json_string) == self.obj_2, "Complex JSON format export / import fails!"

    def test_complex_yaml(self) -> None:
        obj2_yaml_string = str(self.obj_2.to_format("yaml"))
        assert self.obj_2.from_format(obj2_yaml_string, "yaml") == self.obj_2, (
            "Complex YAML format export / import fails!"
        )

    def test_unicode_json(self) -> None:
        obj3_json_string = str(self.obj_3.to_format())  # default format is JSON, make sure this is true
        assert self.obj_3.from_format(obj3_json_string) == self.obj_3, "Unicode JSON format export / import fails!"

    def test_unicode_yaml(self) -> None:
        obj3_yaml_string = str(self.obj_3.to_format("yaml"))
        assert self.obj_3.from_format(obj3_yaml_string, "yaml") == self.obj_3, (
            "Unicode YAML format export / import fails!"
        )

    def test_unicode_json_file(self) -> None:
        with (
            open(os.path.join(self.module_dir, "test_reference.json")) as f,
            open("test.json", **ENCODING_PARAMS) as f2,
        ):
            obj1 = json.load(f)
            obj2 = json.load(f2)
            assert obj1 == obj2, "Unicode JSON file export fails"

        assert self.obj_3.from_file("test.json") == self.obj_3, "Unicode JSON file import fails!"

    def test_unicode_yaml_file(self) -> None:
        ref_path = os.path.join(self.module_dir, "test_reference.yaml")
        with open(ref_path, **ENCODING_PARAMS) as f, open("test.yaml", **ENCODING_PARAMS) as f2:
            assert f.read() == f2.read(), "Unicode JSON file export fails"

        assert self.obj_3.from_file("test.yaml") == self.obj_3, "Unicode YAML file import fails!"

    def test_implicit_serialization(self) -> None:
        assert load_object({"a": {"p1": {"p2": 3}}, "_fw_name": "TestSerializer Export Name"}) == self.obj_4, (
            "Implicit import fails!"
        )

    def test_as_dict(self) -> None:
        assert self.obj_1.as_dict() == self.obj_1.to_dict()

    def test_numpy_array(self) -> None:
        x = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        x = recursive_dict(x)
        assert x == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


class ExplicitSerializationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.s_obj = ExplicitTestSerializer(1)
        self.s_dict = self.s_obj.to_dict()

    def test_explicit_serialization(self) -> None:
        assert load_object(self.s_dict) == self.s_obj


class FWSerializationErrorTest(unittest.TestCase):
    """Test FWSerializationError exception."""

    def setUp(self):
        self.init_dir = os.getcwd()
        self.lpad_dir = mkdtemp()
        os.chdir(self.lpad_dir)
        self.lpad_file = os.path.join(self.lpad_dir, "launchpad.yaml")
        with open(self.lpad_file, "w", encoding="utf-8"):
            pass
        self.msg = "Serialized object must be a dict but is <class 'NoneType'>"

    def tearDown(self):
        os.chdir(self.init_dir)
        os.unlink(self.lpad_file)
        os.rmdir(self.lpad_dir)

    def test_load_object_from_file_empty_file(self) -> None:
        """Test load_object_from_file with empty file."""
        with pytest.raises(FWSerializationError, match=self.msg):
            load_object_from_file(self.lpad_file)

    def test_explicit_serializer_from_file_empty_file(self) -> None:
        """Test ExplicitTestSerializer with empty file."""
        with pytest.raises(FWSerializationError, match=self.msg):
            ExplicitTestSerializer.from_file(self.lpad_file)


class FWFormatErrorTest(unittest.TestCase):
    """Test FWFormatError exception."""

    def setUp(self):
        self.init_dir = os.getcwd()
        self.lpad_dir = mkdtemp()
        os.chdir(self.lpad_dir)
        self.lpad_file = os.path.join(self.lpad_dir, "launchpad.txt")
        with open(self.lpad_file, "w", encoding="utf-8"):
            pass
        self.msg1 = "Unsupported format txt"
        self.msg2 = "Unknown file format txt cannot be loaded!"

    def tearDown(self):
        os.chdir(self.init_dir)
        os.unlink(self.lpad_file)
        os.rmdir(self.lpad_dir)

    def test_explicit_serializer_from_file(self) -> None:
        """Test ExplicitTestSerializer from txt file."""
        with pytest.raises(FWFormatError, match=self.msg1):
            ExplicitTestSerializer.from_file(self.lpad_file)

    def test_explicit_serializer_to_file(self) -> None:
        """Test ExplicitTestSerializer to txt file."""
        with pytest.raises(FWFormatError, match=self.msg1):
            ExplicitTestSerializer(a=1).to_file(self.lpad_file)

    def test_explicit_serializer_to_format(self) -> None:
        """Test ExplicitTestSerializer to txt file."""
        with pytest.raises(FWFormatError, match=self.msg1):
            ExplicitTestSerializer(a=1).to_format("txt")

    def test_load_object_from_file(self) -> None:
        """Test load_object_from_file with txt file."""
        with pytest.raises(FWFormatError, match=self.msg2):
            load_object_from_file(self.lpad_file)
