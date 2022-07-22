#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the URL signal type.
"""

import typing as t

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.url import URLContent
from threatexchange.signal_type import signal_base
from threatexchange.exchanges.impl.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)


class URLSignal(
    signal_base.SimpleSignalType,
    signal_base.MatchesStr,
    HasFbThreatExchangeIndicatorType,
):
    """
    Wrapper around URL links, such as https://github.com/
    """

    INDICATOR_TYPE = ("URI", "RAW_URI")

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [URLContent]

    @classmethod
    def matches_str(
        cls, signal: str, haystack: str, distance_threshold: t.Optional[int] = None
    ) -> signal_base.HashComparisonResult:
        # TODO - normalization
        return signal_base.HashComparisonResult.from_bool(signal == haystack)

    @staticmethod
    def get_examples() -> t.List[str]:
        return ["https://developers.facebook.com/docs/threat-exchange/reference/apis/"]
