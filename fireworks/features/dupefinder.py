# coding: utf-8

from __future__ import unicode_literals

"""
This module contains the base class for implementing Duplicate Finders
"""
import abc

from fireworks.utilities.fw_serializers import serialize_fw, FWSerializable

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Mar 01, 2013'


class DupeFinderBase(FWSerializable):
    """
    This serves an Abstract class for implementing Duplicate Finders
    """

    def __init__(self):
        pass

    def verify(self, spec1, spec2):
        """
        Method that checks whether two specs are identical enough to be considered duplicates. Return true if duplicated.
        :param spec1: (dict)
        :param spec2: (dict)
        """
        raise NotImplementedError

    def query(self, spec):
        """
        Given a spec, returns a database query that gives potential candidates for duplicated FireWorks.

        :param spec: spec to check for duplicates
        """
        raise NotImplementedError

    @serialize_fw
    def to_dict(self):
        return {}

    @classmethod
    def from_dict(cls, m_dict):
        return cls()
