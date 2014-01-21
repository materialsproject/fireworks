#!/usr/bin/env python

"""
TODO: add docs
"""
from fireworks.utilities.fw_serializers import FWSerializable, serialize_fw


__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 26, 2013"


class ExplicitTestSerializer(FWSerializable):
    _fw_name = '{{fireworks.utilities.tests.test_serializer.ExplicitTestSerializer}}'

    def __init__(self, a):
        self.a = a

    def __eq__(self, other):
        return self.a == other.a

    def to_dict(self):
        return {"_fw_name": self._fw_name, "a": self.a}

    @classmethod
    def from_dict(cls, m_dict):
        return ExplicitTestSerializer(m_dict["a"])