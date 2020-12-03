#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Core abstractions for signal types.
"""

import csv
import pathlib
import re
import typing as t

from .. import common
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

    def process_indicator(self, indicator: t.Dict[int, t.Any]) -> bool:
        """
        Add ThreatIndicator to the state of this type, if it is for this type.

        Return true if the indicator was used.
        """
        return False

    def load(self, path: pathlib.Path) -> None:
        raise NotImplementedError

    def load_indicators(self, path: pathlib.Path) -> None:
        if not path.exists():
            return
        csv.field_size_limit(path.stat().st_size)  # dodge field size problems
        with path.open("r", newline="") as f:
            for row in csv.reader(f):
                ti = ThreatIndicator.from_row(row)
                self.indicator_state[ti.id] = ti

    def store(self, path: pathlib.Path) -> None:
        raise NotImplementedError

    def store_indicators(self, path: pathlib.Path) -> None:
        with path.open("w+", newline="") as f:
            writer = csv.writer(f)
            for _, i in self.indicator_state.items():
                writer.writerow(i.as_row())


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
        self.indicator_state: t.Dict[int, ThreatIndicator] = {}

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

    def process_indicator(self, indicator: ThreatIndicator) -> bool:
        """
        Add ThreatIndicator to the state of this type, if it is for this type

        Return true if the indicator was used.
        """
        if (
            indicator.threat_type != self.INDICATOR_TYPE
            or self.TYPE_TAG not in indicator.tags
        ):
            return False

        self.indicator_state[indicator.id] = indicator

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
            for row in csv.reader(f):
                self.state[row[0]] = SimpleDescriptorRollup.from_row(row[1:])

    def store(self, path: pathlib.Path) -> None:
        with path.open("w+", newline="") as f:
            writer = csv.writer(f)
            for k, v in self.state.items():
                writer.writerow((k,) + v.as_row())
