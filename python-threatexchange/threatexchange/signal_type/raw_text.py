#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the raw text signal type.
"""

from dataclasses import dataclass
import typing as t

import Levenshtein

from threatexchange import common
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.text import TextContent
from threatexchange.signal_type import signal_base
from threatexchange.signal_type import index
from threatexchange.exchanges.impl.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)


@dataclass
class RawTextDistance(index.SignalSimilarityInfo):
    """
    Even though we use simple int thresholds, display as a 0-100% match.

    We re-project it onto the length of the query string.
    """

    distance: int
    query_str_len: int

    @property
    def diff_fraction(self) -> float:
        """0.0 -> 1.0 how different query was from target"""
        return min(self.distance, self.query_str_len) / max(1, self.query_str_len)

    @property
    def match_fraction(self) -> float:
        """0.0 -> 1.0 roughly what percent of the string matched"""
        return 1 - self.diff_fraction

    @classmethod
    def from_levenshtein(cls, needle: str, distance: int) -> "RawTextDistance":
        return cls(distance, len(needle))

    def pretty_str(self) -> str:
        return f"{(self.match_fraction) * 100:.0f}%"


class RawTextSignal(
    signal_base.SimpleSignalType,
    signal_base.MatchesStr,
    HasFbThreatExchangeIndicatorType,
):
    """
    Raw text signal is the same as raw text content: the exact text content.

    Unlike other formats like photos or videos, it is difficult to come
    up with non-reversable hashes of text information which are also effective
    at detecting similar content.
    """

    INDICATOR_TYPE = "TEXT_STRING"

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [TextContent]

    @classmethod
    def matches_str(
        cls, signal: str, haystack: str, pct_diff_threshold: float = 5.0
    ) -> signal_base.SignalComparisonResult:
        assert 0 < pct_diff_threshold <= 100
        a = common.normalize_string(signal)
        b = common.normalize_string(haystack)
        max_match_distance = len(a) - len(a) * (100 - pct_diff_threshold) / 100

        ldiff = abs(len(a) - len(b))

        if ldiff > max_match_distance:
            return signal_base.SignalComparisonResult.from_simple_dist(
                ldiff, max_match_distance
            )

        distance: int = Levenshtein.distance(a, b)
        return signal_base.SignalComparisonResult(
            distance <= max_match_distance,
            RawTextDistance.from_levenshtein(a, distance),
        )

    @classmethod
    def get_index_cls(cls) -> t.Type[index.SignalTypeIndex]:
        return LevenshteinLinearSearch

    @staticmethod
    def get_examples() -> t.List[str]:
        return [
            "The quick brown fox jumps over the lazy dog",
            (
                "We the People of the United States, in Order to form a more "
                "perfect Union, establish Justice, ensure domestic "
                "Tranquility, provide for the common defence, promote the "
                "general Welfare, and secure the Blessings of Liberty to "
                "ourselves and our Posterity, do ordain and establish this "
                "Constitution for the United States of America."
            ),
            "bball now?",
        ]


class LevenshteinLinearSearch(signal_base.TrivialLinearSearchMatchIndex):
    _SIGNAL_TYPE = RawTextSignal
    # Could also convert these on ingestion
