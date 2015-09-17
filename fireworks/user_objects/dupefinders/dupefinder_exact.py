# coding: utf-8

from __future__ import unicode_literals

from fireworks.features.dupefinder import DupeFinderBase

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Mar 01, 2013'


class DupeFinderExact(DupeFinderBase):
    """
    This DupeFinder requires an exact spec match between FireWorks.
    """

    _fw_name = 'DupeFinderExact'

    # TODO: move the logic into query() instead of verify() for better performance
    # TODO: just make the 'prematch' thing be always a list of keys...no custom queries allowed (in theory)

    def verify(self, spec1, spec2):
        return spec1 == spec2
        # return True  # if it matches the query, it doesn't need to be verified; it's an exact match!

    def query(self, spec):
        return {}
        # return {'spec': {'$elemMatch': spec}}
