"""
Data models for ThreatExchange entities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ThreatType(Enum):
    """Types of threats in ThreatExchange."""

    MALWARE = "MALWARE"
    PHISHING = "PHISHING"
    SPAM = "SPAM"
    COMPROMISED_CREDENTIAL = "COMPROMISED_CREDENTIAL"
    MALICIOUS_URL = "MALICIOUS_URL"
    HASH_PDQ = "HASH_PDQ"
    HASH_MD5 = "HASH_MD5"
    HASH_SHA256 = "HASH_SHA256"


class ShareLevel(Enum):
    """Privacy levels for sharing threat data."""

    WHITE = "WHITE"
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


class Status(Enum):
    """Status of a threat descriptor."""

    MALICIOUS = "MALICIOUS"
    SUSPICIOUS = "SUSPICIOUS"
    NON_MALICIOUS = "NON_MALICIOUS"
    UNKNOWN = "UNKNOWN"


@dataclass
class ThreatIndicator:
    """
    Represents a threat indicator in ThreatExchange.

    An indicator is a specific piece of data that represents a threat,
    such as a hash, URL, or IP address.
    """

    id: str
    indicator: str
    type: ThreatType
    creation_time: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert the indicator to a dictionary."""
        return {
            "id": self.id,
            "indicator": self.indicator,
            "type": self.type.value,
            "creation_time": (
                self.creation_time.isoformat() if self.creation_time else None
            ),
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
        }


@dataclass
class ThreatDescriptor:
    """
    Represents a threat descriptor in ThreatExchange.

    A descriptor provides context and metadata about a threat indicator,
    including its status, severity, and sharing level.
    """

    id: str
    indicator: ThreatIndicator
    owner_id: str
    status: Status = Status.UNKNOWN
    share_level: ShareLevel = ShareLevel.AMBER
    description: str = ""
    tags: List[str] = field(default_factory=list)
    creation_time: Optional[datetime] = None
    expire_time: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert the descriptor to a dictionary."""
        return {
            "id": self.id,
            "indicator": self.indicator.to_dict(),
            "owner_id": self.owner_id,
            "status": self.status.value,
            "share_level": self.share_level.value,
            "description": self.description,
            "tags": self.tags,
            "creation_time": (
                self.creation_time.isoformat() if self.creation_time else None
            ),
            "expire_time": (
                self.expire_time.isoformat() if self.expire_time else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ThreatDescriptor":
        """Create a ThreatDescriptor from a dictionary."""
        indicator_data = data.get("indicator", {})
        indicator = ThreatIndicator(
            id=indicator_data.get("id", ""),
            indicator=indicator_data.get("indicator", ""),
            type=ThreatType(indicator_data.get("type", "MALWARE")),
        )

        return cls(
            id=data.get("id", ""),
            indicator=indicator,
            owner_id=data.get("owner_id", ""),
            status=Status(data.get("status", "UNKNOWN")),
            share_level=ShareLevel(data.get("share_level", "AMBER")),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )


@dataclass
class ThreatExchangeMember:
    """Minimal ThreatExchange member model matching the API.

    Fields: `id`, `email`, `name` per the ThreatExchange Member API.
    """

    id: str
    email: Optional[str] = None
    name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ThreatExchangeMember":
        return cls(
            id=data.get("id", ""),
            email=data.get("email"),
            name=data.get("name"),
        )

    def to_dict(self) -> dict:
        return {"id": self.id, "email": self.email, "name": self.name}

