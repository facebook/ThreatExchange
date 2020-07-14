##!/usr/bin/env python

"""
Wrapper around the text content type.
"""
import typing as t

from ..signal_type import raw_text, trend_query, url
from ..signal_type.base import SignalType
from .base import ContentType


class TextContent(ContentType):
    @classmethod
    def get_signal_types(cls) -> t.List[t.Type[SignalType]]:
        return [raw_text.RawTextSignal, trend_query.TrendQuerySignal, url.URLSignal]
