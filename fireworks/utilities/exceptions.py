"""FireWorks exceptions"""


class FireworksException(Exception):
    """base exception for all other FireWorks exceptions"""


class FireworksConfigurationError(FireworksException):
    """raise for errors related to fw_config"""


class FireworksSerializationError(FireworksException):
    """raise for errors related to serialization/deserialization"""
