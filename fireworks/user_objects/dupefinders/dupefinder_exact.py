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

    def query(self, spec):
        """
        Returns the query for matching fireworks with non-zero launches and with exact matching specs.

        Args:
            spec (dict): spec to check for duplicates

        Returns:
            dict: mongo query
      """
        return {"$and": [{"launches": {"$ne": []}}, {"spec": spec}]}
