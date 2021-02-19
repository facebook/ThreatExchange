#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import collections
import csv
import json
import os
import pathlib
import time
import re
import typing as t

from ...api import ThreatExchangeAPI
from ... import threat_updates
from ...descriptor import SimpleDescriptorRollup
from ...dataset import Dataset

# TODO - merge SimpleDescriptorRollup here
class CliIndicatorSerialization(threat_updates.ThreatUpdateSerialization):
    """A short compact serialization optimized for the CLI"""

    def __init__(
        self, indicator_type: str, indicator: str, rollup: SimpleDescriptorRollup
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

    @classmethod
    def store(
        cls, state_dir: pathlib.Path, contents: t.Iterable["CliIndicatorSerialization"]
    ) -> t.List[pathlib.Path]:
        # Stores in multiple files
        row_by_type = collections.defaultdict(list)
        for item in contents:
            row_by_type[item.indicator_type].append(item)
        ret = []
        for threat_type, items in row_by_type.items():
            path = state_dir / f"simple.{threat_type}{Dataset.EXTENSION}"
            ret.append(path)
            with path.open("w") as f:
                writer = csv.writer(f)
                writer.writerows(item.as_csv_row() for item in items)
        return ret

    @classmethod
    def load(cls, state_dir: pathlib.Path) -> t.List["ThreatUpdateSerialization"]:
        """Load this serialization from the state directory"""
        ret = []
        pattern = r"simple\.([^.]+)" + re.escape(Dataset.EXTENSION)
        for path in state_dir.glob(f"simple.*{Dataset.EXTENSION}"):
            match = re.match(pattern, path.name)
            if not match or not path.is_file():
                continue
            indicator_type = match.group(1)
            # Violate your warranty with class state! Not threadsafe!
            csv.field_size_limit(path.stat().st_size)  # dodge field size problems
            with path.open("r", newline="") as f:
                for row in csv.reader(f):
                    ret.append(
                        cls(
                            indicator_type,
                            row[0],
                            SimpleDescriptorRollup.from_row(row[1:]),
                        )
                    )
        return ret
