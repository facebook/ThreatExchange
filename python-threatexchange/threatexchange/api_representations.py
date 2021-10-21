# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Typed representations (dataclasses only) for interfacing with the
threatexchange API.
"""

from datetime import datetime
from dateutil.parser import parse
from dataclasses import dataclass
import typing as t


def _parse_datetime_from_iso_8601(datestr: str) -> datetime:
    """
    Parses strings representing date like 2019-05-20T16:44:47+0000 from the
    graph api into datetime objects.
    """
    return parse(datestr)


@dataclass
class ThreatPrivacyGroup:
    id: int
    name: str
    description: str
    members_can_see: bool
    members_can_use: bool
    threat_updates_enabled: bool
    last_updated: datetime

    def __eq__(self, other) -> bool:
        return self.id == other.id

    def __hash__(self) -> bool:
        return hash(self.id)

    @classmethod
    def from_graph_api_dict(cls, d: dict) -> "ThreatPrivacyGroup":
        return cls(
            d["id"],
            d["name"],
            d["description"],
            bool(d["members_can_see"]),
            bool(d["members_can_use"]),
            bool(d["threat_updates_enabled"]),
            _parse_datetime_from_iso_8601(d["last_updated"]),
        )


@dataclass
class CSPFeedback:
    source: str
    feedbackValue: str
    tags: t.List[str]

    @classmethod
    def from_dict(cls, d: dict) -> "CSPFeedback":
        return cls(
            d.get("source", None),
            d.get("feedbackValue", None),
            d.get("tags", []),
        )


@dataclass
class HashRecord:
    lastModtimestamp: datetime
    hashValue: str
    hashStatus: str
    signalType: str
    caseNumbers: t.Dict[str, str]
    tags: t.List[str]
    hashRegions: t.List[str]
    CSPFeedbacks: t.List[CSPFeedback]

    def __eq__(self, other) -> bool:
        return self.hashValue == other.hashValue

    def __hash__(self) -> bool:
        return hash(self.hashValue)

    @classmethod
    def from_dict(cls, d: dict) -> "HashRecord":
        return cls(
            lastModtimestamp=datetime.fromtimestamp(d.get("lastModtimestamp", None)),
            hashValue=d.get("hashValue", None),
            hashStatus=d.get("hashStatus", None),
            signalType=d.get("signalType", None),
            caseNumbers=d.get("caseNumbers", {}),
            tags=d.get("tags", []),
            hashRegions=d.get("hashRegions", []),
            CSPFeedbacks=[CSPFeedback.from_dict(x) for x in d.get("CSPFeedbacks", [])],
        )
