"""FireWorks exceptions."""


class FWError(Exception):
    """Base exception for all other FireWorks exceptions."""


class FWConfigurationError(FWError):
    """Raise for errors related to fw_config."""


class FWSerializationError(FWError):
    """Raise for errors related to serialization/deserialization."""


class FWFormatError(FWError):
    """Raise for errors related to file format."""


class FWValueError(FWError, ValueError):
    """FireWorks specialization of ValueError."""
