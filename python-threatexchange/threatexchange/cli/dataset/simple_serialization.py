#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import collections
import csv
import pathlib
import re
import typing as t

from threatexchange.exchanges.clients.fb_threatexchange import threat_updates
from threatexchange.exchanges.clients.fb_threatexchange.descriptor import (
    SimpleDescriptorRollup,
)

_EXTENSION = ".te"

# TODO - merge SimpleDescriptorRollup here
class CliIndicatorSerialization(threat_updates.ThreatUpdateSerialization):
    """A short compact serialization optimized for the CLI"""

    def __init__(
        self,
        indicator_type: str,
        indicator: str,
        rollup: SimpleDescriptorRollup,
    ):
        self.indicator_type = indicator_type
        self.indicator = indicator
        self.rollup = rollup

    @property
    def key(self):
        return f"{self.indicator_type}.{self.indicator}"

    def as_csv_row(self) -> t.Tuple:
        """As a simple record type for the threatexchange CLI cache"""
        return (self.indicator,) + self.rollup.as_row()

    @classmethod
    def from_threat_updates_json(cls, app_id, te_json):
        return cls(
            te_json["type"],
            te_json["indicator"],
            SimpleDescriptorRollup.from_threat_updates_json(app_id, te_json),
        )

    @classmethod
    def te_threat_updates_fields(cls):
        return SimpleDescriptorRollup.te_threat_updates_fields()

    # ToDo this violates Liskov but is already used in Prod and will require a larger refactor
    @classmethod
    def store(
        cls, state_dir: pathlib.Path, contents: t.Iterable["CliIndicatorSerialization"]
    ) -> t.List[pathlib.Path]:
        # Stores in multiple files split by indicator type
        row_by_type = collections.defaultdict(list)
        for item in contents:
            row_by_type[item.indicator_type].append(item)
        ret = []
        for threat_type, items in row_by_type.items():
            path = state_dir / f"simple.{threat_type}{_EXTENSION}"
            ret.append(path)
            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                for item in items:
                    writer.writerow(item.as_csv_row())
        return ret

    @classmethod
    def load(cls, state_dir: pathlib.Path) -> t.Iterable["CliIndicatorSerialization"]:
        """Load this serialization from the state directory"""
        ret = []
        pattern = r"simple\.([^.]+)" + re.escape(_EXTENSION)
        for path in state_dir.glob(f"simple.*{_EXTENSION}"):
            match = re.match(pattern, path.name)
            if not match or not path.is_file():
                continue
            indicator_type = match.group(1)
            # Violate your warranty with class state! Not threadsafe!
            csv.field_size_limit(path.stat().st_size)  # dodge field size problems
            with path.open("r", encoding="utf-8", newline="") as f:
                for row in csv.reader(f):
                    ret.append(
                        cls(
                            indicator_type,
                            row[0],
                            SimpleDescriptorRollup.from_row(row[1:]),
                        )
                    )
        return ret


class HMASerialization(CliIndicatorSerialization):
    """
    A Serialization for HMA Similar to CliIndicatorSerialization but with
    Indicator ID.

    We also include the First Descriptor ID. The logic to determine which ID
    this is can be found in the SimpleDescriptorRollup
    """

    def __init__(
        self,
        indicator: str,
        indicator_type: str,
        indicator_id: str,
        rollup: SimpleDescriptorRollup,
    ):
        self.indicator_id = indicator_id
        self.indicator_type = indicator_type
        self.indicator = indicator
        self.rollup = rollup

    def as_csv_row(self) -> t.Tuple:
        """indicator details and descriptor rollup without descriptor ID"""
        return (self.indicator, self.indicator_id) + self.rollup.as_row()

    @classmethod
    def from_threat_updates_json(cls, app_id, te_json):
        return cls(
            te_json["indicator"],
            te_json["type"],
            te_json["id"],
            SimpleDescriptorRollup.from_threat_updates_json(app_id, te_json),
        )

    @classmethod
    def from_csv_row(
        cls, row: t.List[t.Any], indicator_type: str
    ) -> "HMASerialization":
        return cls(
            str(row[0]),
            indicator_type,
            str(row[1]),
            SimpleDescriptorRollup.from_row(row[2:]),
        )

    @classmethod
    def load(cls, state_dir: pathlib.Path) -> t.Iterable["HMASerialization"]:
        """Load this serialization from the state directory"""
        ret = []
        pattern = r"simple\.([^.]+)" + re.escape(_EXTENSION)
        for path in state_dir.glob(f"simple.*{_EXTENSION}"):
            match = re.match(pattern, path.name)
            if not match or not path.is_file():
                continue
            indicator_type = match.group(1)
            # Violate your warranty with class state! Not threadsafe!
            csv.field_size_limit(path.stat().st_size)  # dodge field size problems
            with path.open("r", newline="") as f:
                for row in csv.reader(f):
                    ret.append(cls.from_csv_row(row, indicator_type))
        return ret


if __name__ == "__main__":
    # Test Serialize Deserialize
    indicator = "indicator"
    indicator_id = "12345"
    first_descriptor_id = 6789
    added_on = "today"
    labels = {"tag1", "tag2"}

    ser = HMASerialization(
        indicator,
        "HASH_PDQ",
        indicator_id,
        SimpleDescriptorRollup(first_descriptor_id, added_on, labels),
    )
    serdeser = HMASerialization.from_csv_row(list(ser.as_csv_row()), "HASH_PDQ")

    if ser.as_csv_row() == serdeser.as_csv_row():
        print("Serialization worked correctly")
    else:
        print("Serialization failed")
