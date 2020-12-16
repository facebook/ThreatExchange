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
      "should_delete": false,
      "tags": [
        "tag1",
        "tag2",
        "tag3"
      ],
      "applications_with_opinions": [
        "123456789055502"
      ],
    }
    """

    id: int
    indicator: str
    threat_type: str
    creation_time: int
    last_updated: int
    status: str
    should_delete: bool
    tags: t.List[str]
    applications_with_opinions: t.List[int]

    def as_row(self) -> t.Tuple[int, str, str, int, int, str, str, str]:
        """Simple conversion to CSV row"""
        return (
            self.id,
            self.indicator,
            self.threat_type,
            self.creation_time,
            self.last_updated,
            self.status,
            " ".join(self.tags),
            " ".join([str(app) for app in self.applications_with_opinions]),
        )

    @classmethod
    def from_row(self, row: t.Iterable) -> "ThreatIndicator":
        """Simple conversion from CSV row"""
        last_updated = int(row[4]) if row[4] else None
        # should_delete isn't saved in the CSV as if it is true we delete the record
        # so all loaded descriptors should have a should_delete value of False
        should_delete = False
        tags = row[6].split(" ") if row[6] else []
        apps = [int(app) for app in (row[7].split(" ") if row[7] else [])]
        return ThreatIndicator(
            int(row[0]),
            row[1],
            row[2],
            int(row[3]),
            last_updated,
            row[5],
            should_delete,
            tags,
            apps,
        )
