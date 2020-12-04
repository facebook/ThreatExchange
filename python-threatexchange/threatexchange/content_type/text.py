#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the text content type.
"""
import typing as t

from ..signal_type import raw_text, trend_query, url
from ..signal_type.signal_base import SignalType
from .content_base import ContentType


class TextContent(ContentType):
    """
    Content that represents static blobs of text.

    Examples might be:
    * Posts
    * Profile descriptions
    * OCR from photos, if the text itself is the dominating element
      (i.e. a screenshot of a block of text)
    """

    @classmethod
    def get_signal_types(cls) -> t.List[t.Type[SignalType]]:
        return [raw_text.RawTextSignal, trend_query.TrendQuerySignal, url.URLSignal]
