"""FireWorks exceptions"""


class FWException(Exception):
    """base exception for all other FireWorks exceptions"""


class FWConfigurationError(FWException):
    """raise for errors related to fw_config"""


class FWSerializationError(FWException):
    """raise for errors related to serialization/deserialization"""


class FWFormatError(FWException):
    """raise for errors related to file format"""
