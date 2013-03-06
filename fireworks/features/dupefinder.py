from fireworks.utilities.fw_serializers import serialize_fw, FWSerializable

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Mar 01, 2013'


class DupeFinderBase(FWSerializable):
    """
    TODO: add docs
    """

    def __init__(self):
        pass

    def verify(self, spec1, spec2):
        raise NotImplementedError

    def query(self, spec):
        raise NotImplementedError

    @serialize_fw
    def to_dict(self):
        return {}

    @classmethod
    def from_dict(cls, m_dict):
        return cls()
