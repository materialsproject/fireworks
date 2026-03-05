"""Helpers used in unit tests to validate serialization behavior."""

from __future__ import annotations

import datetime
from typing import Any

from fireworks.utilities.fw_serializers import FWSerializable, serialize_fw

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2014, The Materials Project"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 21, 2014"


class UnitTestSerializer(FWSerializable):
    """Serializable object used for testing round-trip serialization."""

    _fw_name = "TestSerializer Name"
    __hash__ = None

    def __init__(self, a: Any, m_date: datetime.datetime) -> None:
        """Construct with a generic payload and a datetime stamp."""
        if not isinstance(m_date, datetime.datetime):
            raise TypeError("m_date must be a datetime instance!")

        self.a = a
        self.m_date = m_date

    def __eq__(self, other: object) -> bool:
        """Return True if payload and timestamp are equal."""
        if not isinstance(other, UnitTestSerializer):
            return NotImplemented
        return self.a == other.a and self.m_date == other.m_date

    @serialize_fw
    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict for FireWorks."""
        return {"a": self.a, "m_date": self.m_date}

    @classmethod
    def from_dict(cls, m_dict: dict[str, Any]) -> UnitTestSerializer:
        """Recreate instance from a serialized dict."""
        return cls(m_dict["a"], m_dict["m_date"])


class ExportTestSerializer(FWSerializable):
    """Serializer to test exporting with explicit _fw_name entries."""

    _fw_name = "TestSerializer Export Name"
    __hash__ = None

    def __init__(self, a: Any) -> None:
        """Construct with a generic payload."""
        self.a = a

    def __eq__(self, other: object) -> bool:
        """Return True if payloads are equal."""
        if not isinstance(other, ExportTestSerializer):
            return NotImplemented
        return self.a == other.a

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict including the FireWorks name."""
        return {"a": self.a, "_fw_name": self.fw_name}

    @classmethod
    def from_dict(cls, m_dict: dict[str, Any]) -> ExportTestSerializer:
        """Recreate instance from a serialized dict."""
        return cls(m_dict["a"])
