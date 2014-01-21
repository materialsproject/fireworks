#!/usr/bin/env python

"""
This module contains the base class for implementing Duplicate Finders
"""
import abc

from fireworks.utilities.fw_serializers import serialize_fw, FWSerializable, get_default_serialization

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Mar 01, 2013'


class DupeFinderMeta(type):

    __metaclass__ = abc.ABCMeta

    def __init__(cls, name, bases, dct):
        # Set default _fw_name to be a space separated version of the class
        # name.
        if name != "DupeFinderBase" and not hasattr(cls, "_fw_name"):
            cls._fw_name = get_default_serialization(cls)
        type.__init__(cls, name, bases, dct)

class DupeFinderBase(dict, FWSerializable):  # extending dict only to use metaclass - UGLY!
    """
    This serves an Abstract class for implementing Duplicate Finders
    """
    __metaclass__ = DupeFinderMeta

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