#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Core abstractions for signal types.
"""

import csv
import os
import pathlib
import re
import typing as t

from .. import common
from .. import dataset
from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from ..indicator import ThreatIndicator


class SignalMatch(t.NamedTuple):
    # TODO - Labels probably don't belong here, because we just duplicate storage
    #        better to have descriptor lookup with the full labels
    labels: t.Set[str]
    primary_descriptor_id: int
    # TODO: Someday, also include the following:
    # contested: bool
    # plurality_opinion: t.Tuple(bool, t.Set[str])
    # highest_action_severity: str
    # opinions_by_owner: t.Dict[int, MatchOpinion]


class SignalType:
    """
    Abstraction for different signal types.

    A signal type is an intermediate representation of content that can be used
    to match against similar or identical content. Sometimes called a "hash"
    type.

    This class additionally helps translates ThreatDescriptors into the correct
    representation to do matching, as well as serialize that representation
    into a compact form.
    """

    @classmethod
    def get_name(cls):
        """A compact name in lower_with_underscore style (used in filenames)"""
        return common.class_name_to_human_name(cls.__name__, "Signal")

    def process_descriptor(self, descriptor: t.Dict[str, t.Any]) -> bool:
        """
        Add ThreatDescriptor to the state of this type, if it is for this type.

        Return true if the true if the descriptor was used.
        """
        return False

    def load(self, path: pathlib.Path) -> None:
        raise NotImplementedError

    def store(self, path: pathlib.Path) -> None:
        raise NotImplementedError


class IndicatorSignals:
    """
    A class to load and store ThreatIndicators.
    """

    def __init__(self, state_dir: pathlib.Path, privacy_group: int) -> None:
        self.sub_dir = "indicators"
        self.privacy_group = str(privacy_group)
        self.state: t.Dict[str, t.Dict[int, ThreatIndicator]] = {}
        self.path = state_dir / self.sub_dir / self.privacy_group

    def process_indicator(self, indicator: ThreatIndicator) -> None:
        if indicator.threat_type not in self.state:
            self.state[indicator.threat_type] = {}

        self.state[indicator.threat_type][indicator.id] = indicator
        if indicator.should_delete:
            del self.state[indicator.threat_type][indicator.id]

    def store_indicators(self) -> None:
        os.makedirs(self.path, exist_ok=True)
        for threat_type in self.state:
            store = self.path / f"{threat_type}{dataset.Dataset.EXTENSION}"
            with store.open("w+", newline="") as s:
                writer = csv.writer(s)
                for _, i in self.state[threat_type].items():
                    writer.writerow(i.as_row())

    def load_indicators(self) -> None:
        # No state directory = no state
        if not self.path.exists:
            return
        for store in self.path.glob(f"[!_]*{dataset.Dataset.EXTENSION}"):
            csv.field_size_limit(store.stat().st_size)  # dodge field size problems
            with store.open("r", newline="") as s:
                try:
                    for row in csv.reader(s):
                        ti = ThreatIndicator.from_row(row)
                        self.process_indicator(ti)
                except Exception as e:
                    print(f"Encountered {e} while loading an indicator from {store}")


class HashMatcher:
    def match_hash(self, hash: str) -> t.List[SignalMatch]:
        """
        Given a representation of this SignalType, return matches.

        Example - PDQ distance comparison, or MD5 exact comparison
        """
        raise NotImplementedError


class FileMatcher:
    def match_file(self, file: pathlib.Path) -> t.List[SignalMatch]:
        """
        Given a file containing content, return matches.
        """
        raise NotImplementedError


class StrMatcher(FileMatcher):
    def match(self, content: str) -> t.List[SignalMatch]:
        """
        Given a string representation of content, return matches.

        You don't need to implement this if it doesn't make sense for your
        signal type.
        """
        raise NotImplementedError

    def match_file(self, path: pathlib.Path) -> t.List[SignalMatch]:
        return self.match(path.read_text())


class SimpleSignalType(SignalType, HashMatcher):
    """
    Dead simple implementation for loading/storing a SignalType.

    Assumes that the signal type can easily merge on a string.
    """

    INDICATOR_TYPE = ""
    TYPE_TAG = ""

    def __init__(self) -> None:
        self.state: t.Dict[str, SimpleDescriptorRollup] = {}

    def process_descriptor(self, descriptor: ThreatDescriptor) -> bool:
        """
        Add ThreatDescriptor to the state of this type, if it is for this type

        Return true if the true if the descriptor was used.
        """
        if (
            descriptor.indicator_type != self.INDICATOR_TYPE
            or self.TYPE_TAG not in descriptor.tags
        ):
            return False
        old_val = self.state.get(descriptor.raw_indicator)
        if old_val is None:
            self.state[
                descriptor.raw_indicator
            ] = SimpleDescriptorRollup.from_descriptor(descriptor)
        else:
            old_val.merge(descriptor)
        return True

    def match_hash(self, signal_str: str) -> t.List[SignalMatch]:
        found = self.state.get(signal_str)
        if found:
            return [SignalMatch(found.labels, found.first_descriptor_id)]
        return []

    def load(self, path: pathlib.Path) -> None:
        self.state.clear()
        csv.field_size_limit(path.stat().st_size)  # dodge field size problems
        with path.open("r", newline="") as f:
            try:
                for row in csv.reader(f):
                    self.state[row[0]] = SimpleDescriptorRollup.from_row(row[1:])
            except Exception as e:
                print(e)

    def store(self, path: pathlib.Path) -> None:
        with path.open("w+", newline="") as f:
            writer = csv.writer(f)
            for k, v in self.state.items():
                writer.writerow((k,) + v.as_row())
