#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the Trend Query (keywords and regexes) content type.
"""

import csv
import json
import pathlib
import re
import typing as t

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import signal_base


class TrendQuery:
    """
    A parsed trend query, based on regexes.
    """

    REGEX_PREFIX = "regex-"

    # re.pattern is not in 3.6, which is what we are targeting right now
    def __init__(self, query_json: t.Dict[str, t.Any]) -> None:
        self.and_terms: t.List[t.List[t.Any]] = [
            [self._parse_term(t) for t in and_["or"]] for and_ in query_json["and"]
        ]
        self.not_terms: t.List[t.Any] = [self._parse_term(t) for t in query_json["not"]]

    def _parse_term(self, t) -> t.Any:
        if t.startswith(self.REGEX_PREFIX):
            return re.compile(t[len(self.REGEX_PREFIX) + 1 : -1])
        return re.compile(f"\\b{re.escape(t)}\\b")

    def _match_term(self, t: t.Union[str, t.Any], text: str) -> bool:
        return bool()

    def matches(self, text: str) -> bool:
        for or_ in self.and_terms:
            if not any(t.search(text) for t in or_):
                break
        else:
            return not any(t.search(text) for t in self.not_terms)
        return False


class TrendQuerySignal(signal_base.SignalType, signal_base.StrMatcher):
    """
    Trend Queries are a combination of and/or/not regexes.

    Based off a system effective for grouping content at Facebook, Trend Queries
    can potentially help you sift though large sets of content to quickly flag
    ones that might be interesting to you.

    They have high "recall" but potentially low "precision".
    """

    def __init__(self) -> None:
        self.state: t.Dict[str, t.Tuple[TrendQuery, SimpleDescriptorRollup]] = {}

    def process_descriptor(self, descriptor: ThreatDescriptor) -> bool:
        """
        Add ThreatDescriptor to the state of this type, if it is for this type

        Return true if the true if the descriptor was used.
        """
        if (
            descriptor.indicator_type != "DEBUG_STRING"
            or "media_type_trend_query" not in descriptor.tags
        ):
            return False
        old_val = self.state.get(descriptor.raw_indicator)
        query_json = json.loads(descriptor.raw_indicator)

        if old_val is None:
            self.state[descriptor.raw_indicator] = (
                TrendQuery(query_json),
                SimpleDescriptorRollup(
                    descriptor.id,
                    descriptor.added_on,
                    set(descriptor.tags),
                ),
            )
        else:
            old_val[1].merge(descriptor)
        return True

    def match(self, content: str) -> t.List[signal_base.SignalMatch]:
        return [
            signal_base.SignalMatch(rollup.labels, rollup.first_descriptor_id)
            for query, rollup in self.state.values()
            if query.matches(content)
        ]

    def load(self, path: pathlib.Path) -> None:
        self.state.clear()
        csv.field_size_limit(path.stat().st_size)  # dodge field size problems
        with path.open("r", newline="") as f:
            for row in csv.reader(f, dialect="excel-tab"):
                raw_indicator = row[0]
                query_json = json.loads(raw_indicator)
                self.state[raw_indicator] = (
                    TrendQuery(query_json),
                    SimpleDescriptorRollup.from_row(row[1:]),
                )

    def store(self, path: pathlib.Path) -> None:
        with path.open("w+", newline="") as f:
            writer = csv.writer(f, dialect="excel-tab")
            for k, v in self.state.items():
                writer.writerow((k,) + v[1].as_row())

    @classmethod
    def indicator_applies(cls, indicator_type: str, tags: t.List[str]) -> bool:
        return indicator_type == "DEBUG_STRING" and "media_type_trend_query" in tags
