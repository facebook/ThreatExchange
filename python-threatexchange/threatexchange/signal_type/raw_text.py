#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the raw text signal type.
"""

import math
import pathlib
import typing as t

import Levenshtein

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from .. import common
from . import signal_base


class RawTextSignal(signal_base.SimpleSignalType, signal_base.StrMatcher):
    """
    Raw text signal is the same as raw text content: the exact text content.

    Unlike other formats like photos or videos, it is difficult to come
    up with non-reversable hashes of text information which are also effective
    at detecting similar content.
    """

    INDICATOR_TYPE = "DEBUG_STRING"
    TYPE_TAG = "media_type_text"

    def __init__(self) -> None:
        super().__init__()
        self.normal_to_raw: t.Dict[str, str] = {}

    def match(self, content: str) -> t.List[signal_base.SignalMatch]:
        return self.match_hash(content)

    def match_hash(self, signal_str: str) -> t.List[signal_base.SignalMatch]:
        normalized_str = common.normalize_string(signal_str)
        # Match considered if 95% match
        match_threshold = math.floor(len(normalized_str) * 0.05)
        matches = []
        for normalized_candidate, raw in self.normal_to_raw.items():
            ldiff = abs(len(normalized_candidate) - len(normalized_str))
            # Filter out anything that can't possibly match due to len difference
            # Could optimize this if needed by storing in length buckets/sorted by length
            # (What about text content fully contained in target?)
            if ldiff > match_threshold:
                continue
            distance = Levenshtein.distance(normalized_candidate, normalized_str)
            # Linear search for fun and profit (but not efficiency)
            if distance <= match_threshold:
                found = self.state[raw]
                matches.append(
                    signal_base.SignalMatch(found.labels, found.first_descriptor_id)
                )
        return matches

    def process_descriptor(self, descriptor: ThreatDescriptor) -> bool:
        if not super().process_descriptor(descriptor):
            return False
        self._postprocess_indicator(descriptor.raw_indicator)
        return True

    def _postprocess_indicator(self, indicator: str) -> None:
        normalized = common.normalize_string(indicator)
        self.normal_to_raw[common.normalize_string(normalized)] = indicator

    def load(self, path: pathlib.Path) -> None:
        super().load(path)
        for indicator in self.state:
            self._postprocess_indicator(indicator)
