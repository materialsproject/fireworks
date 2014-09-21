# coding: utf-8

from __future__ import unicode_literals

import datetime
from fireworks.utilities.fw_serializers import FWSerializable, serialize_fw

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2014, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Jan 21, 2014'


class TestSerializer(FWSerializable):
    _fw_name = 'TestSerializer Name'

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
    def from_dict(cls, m_dict):
        return TestSerializer(m_dict["a"], m_dict["m_date"])


class ExportTestSerializer(FWSerializable):
    _fw_name = 'TestSerializer Export Name'

    def __init__(self, a):
        self.a = a

    def __eq__(self, other):
        return self.a == other.a

    def to_dict(self):
        return {"a": self.a, "_fw_name": self.fw_name}

    @classmethod
    def from_dict(cls, m_dict):
        return ExportTestSerializer(m_dict["a"])
