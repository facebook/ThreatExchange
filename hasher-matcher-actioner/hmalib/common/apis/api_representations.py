# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Typed representations (dataclasses only) for interfacing with the
API classes.
"""

from datetime import datetime
from dataclasses import dataclass
import typing as t


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
