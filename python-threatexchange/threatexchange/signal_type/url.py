#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the URL signal type.
"""

import typing as t

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.url import URLContent
from threatexchange.signal_type import signal_base


class URLSignal(signal_base.SimpleSignalType, signal_base.TrivialTextHasher):
    """
    Wrapper around URL links, such as https://github.com/
    """

    INDICATOR_TYPE = ("URI", "RAW_URI")

    @classmethod
    def get_content_types(self) -> t.List[t.Type[ContentType]]:
        return [URLContent]

    @staticmethod
    def get_examples() -> t.List[str]:
        return ["https://developers.facebook.com/docs/threat-exchange/reference/apis/"]
