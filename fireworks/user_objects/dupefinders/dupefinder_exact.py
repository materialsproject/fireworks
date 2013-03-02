__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Mar 01, 2013'


class DupeFinderExact():
    """
    TODO: add docs
    """


    # TODO: move the logic into query() instead of verify() for better performance
    
    def verify(self, spec1, spec2):
        return spec1 == spec2

    def query(self):
        return {}