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

    INDICATOR_TYPE = {"URI", "RAW_URI"}

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [URLContent]

    @classmethod
    def get_index_cls(cls) -> t.Type[signal_base.TrivialSignalTypeIndex]:
        # TODO - There are a lot more considerations than this
        #        as well as normalizations that could be applied
        return signal_base.TrivialSignalTypeIndex

    @classmethod
    def matches_str(
        cls, signal: str, haystack: str
    ) -> signal_base.SignalComparisonResult:
        # TODO - normalization
        return signal_base.SignalComparisonResult.from_bool_only(signal == haystack)

    @staticmethod
    def get_examples() -> t.List[str]:
        return ["https://developers.facebook.com/docs/threat-exchange/reference/apis/"]

    @classmethod
    def normalize_fb_threatexchange_indicator(
        cls, tx_type: str, tx_indicator: str, tx_tag: t.Optional[str]
    ) -> str:
        if tx_type == "UNCLICKABLE_URL" and tx_indicator.startswith("[h]"):
            return f"h{tx_indicator[3:]}"
        return super().normalize_fb_threatexchange_indicator(
            tx_type, tx_indicator, tx_tag
        )
