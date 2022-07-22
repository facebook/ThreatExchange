#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the URL MD5 signal types.
"""

import typing as t
import hashlib
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.url import URLContent

from threatexchange.signal_type import signal_base
from threatexchange import common
from threatexchange.signal_type.url import URLSignal
from threatexchange.exchanges.impl.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)


class UrlMD5Signal(
    signal_base.SimpleSignalType,
    signal_base.TextHasher,
    HasFbThreatExchangeIndicatorType,
):
    """
    Simple signal type for URL MD5s.
    """

    INDICATOR_TYPE = "HASH_URL_MD5"

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [URLContent]

    @classmethod
    def get_index_cls(cls) -> t.Type[signal_base.TrivialSignalTypeIndex]:
        return signal_base.TrivialSignalTypeIndex

    @classmethod
    def hash_from_str(cls, url: str) -> str:
        encoded_url = common.normalize_url(url)
        url_hash = hashlib.md5(encoded_url)
        return url_hash.hexdigest()

    @staticmethod
    def get_examples() -> t.List[str]:
        return [UrlMD5Signal.hash_from_str(s) for s in URLSignal.get_examples()]
