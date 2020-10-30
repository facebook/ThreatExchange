#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrappers for the json returned by the ThreatExchange API to typed objects.
"""

import typing as t

from . import TE


class ThreatIndicator(t.NamedTuple):
    """
    Wrapper around ThreatExchange JSON for a ThreatIndicator.

    Example:
    {
      "id": "3058061737574159",
      "indicator": "facefacefacefacefacefacefaceface",
      "type": "HASH_PDQ",
      "creation_time": 1601513795,
      "last_updated": 1601513796,
      "status": "MALICIOUS",
      "is_expired": false,
      "tags": [
        "tag1",
        "tag2",
        "tag3"
      ],
      "applications_with_opinions": [
        "123456789055502"
      ],
      "expire_time": 9601513796
    }
    """

    id: int
    indicator: str
    threat_type: str
    creation_time: int
    last_updated: int
    status: str
    is_expired: bool
    tags: t.List[str]
    applications_with_opinions: t.List[int]
    expire_time: int

    def as_row(self) -> t.Tuple[int, str, str, int, int, str, bool, str, str, int]:
        """Simple conversion to CSV row"""
        return (
            self.id,
            self.indicator,
            self.threat_type,
            self.creation_time,
            self.last_updated,
            self.status,
            self.is_expired,
            " ".join(self.tags),
            " ".join([str(app) for app in self.applications_with_opinions]),
            self.expire_time,
        )

    @classmethod
    def from_row(self, row: t.Iterable) -> "ThreatIndicator":
        """Simple conversion from CSV row"""
        tags = row[7].split(" ") if row[7] else []
        apps = [int(app) for app in (row[8].split(" ") if row[8] else [])]
        expire_time = int(row[9]) if row[9] else None
        return ThreatIndicator(
            int(row[0]),
            row[1],
            row[2],
            int(row[3]),
            int(row[4]),
            row[5],
            row[6] == "True",
            tags,
            apps,
            expire_time,
        )
