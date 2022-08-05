#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the Trend Query (keywords and regexes) content type.
"""

import json
import re
import typing as t
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.text import TextContent

from threatexchange.signal_type import signal_base
from threatexchange.signal_type import index
from threatexchange.exchanges.impl.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)


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


class TrendQuerySignal(
    signal_base.SignalType, signal_base.MatchesStr, HasFbThreatExchangeIndicatorType
):
    """
    Trend Queries are a combination of and/or/not regexes.

    Based off a system effective for grouping content at Facebook, Trend Queries
    can potentially help you sift though large sets of content to quickly flag
    ones that might be interesting to you.

    They have high "recall" but potentially low "precision".
    """

    INDICATOR_TYPE = "TREND_QUERY"

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [TextContent]

    @classmethod
    def validate_signal_str(cls, signal_str: str) -> str:
        tq = TrendQuery(
            json.loads(signal_str)
        )  # TODO - does this throw all the right exceptions?
        return signal_str

    @classmethod
    def matches_str(
        cls, hash: str, haystack: str
    ) -> signal_base.SignalComparisonResult:
        tq = TrendQuery(json.loads(hash))
        return signal_base.SignalComparisonResult.from_bool_only(tq.matches(haystack))

    @classmethod
    def get_index_cls(cls) -> t.Type[index.SignalTypeIndex]:
        return TrendQueryIndex

    @staticmethod
    def get_examples() -> t.List[str]:
        return [
            json.dumps(
                {
                    "and": [
                        {
                            "or": [
                                "basketball",
                                "basket ball",
                                "basket-ball",
                                "bball",
                                "hoops",
                            ]
                        },
                        {"or": ["play", "tonight", "today", "now"]},
                    ],
                    "not": ["tomorrow", "baseball", "hockey", "football", "soccer"],
                }
            )
        ]


class TrendQueryIndex(index.SignalTypeIndex[index.T]):
    def __init__(self) -> None:
        self.state: t.Dict[str, t.Tuple[TrendQuery, t.List[index.T]]] = {}

    # TODO - Figure out how to properly capture hash vs search
    def query(self, hash: str) -> t.List[index.IndexMatch[index.T]]:
        ret: t.List[index.IndexMatch[index.T]] = []
        for tq, values in self.state.values():
            if tq.matches(hash):
                ret.extend(
                    index.IndexMatch(index.SignalSimilarityInfo(), v) for v in values
                )
        return ret

    def add(self, hash: str, value: index.T) -> None:
        old_val = self.state.get(hash)
        query_json = json.loads(hash)

        if old_val is None:
            self.state[hash] = (
                TrendQuery(query_json),
                [value],
            )
        else:
            old_val[1].append(value)
