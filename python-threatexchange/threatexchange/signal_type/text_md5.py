#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the Text MD5 signal types.
"""

import typing as t
import hashlib
import pathlib
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.text import TextContent

from threatexchange.signal_type import signal_base
from threatexchange import common
from threatexchange.signal_type.raw_text import RawTextSignal
from threatexchange.fetcher.apis.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)


class TextMD5Signal(
    signal_base.SimpleSignalType,
    signal_base.TextHasher,
    signal_base.FileHasher,
    HasFbThreatExchangeIndicatorType,
):
    """
    Simple signal type for Text MD5s.
    """

    INDICATOR_TYPE = "TEXT_URL_MD5"

    @classmethod
    def get_content_types(self) -> t.List[t.Type[ContentType]]:
        return [TextContent]

    @classmethod
    def hash_from_str(cls, text: str) -> str:
        encoded_text = common.normalize_string(text).encode("utf-8")
        text_hash = hashlib.md5(encoded_text)
        return text_hash.hexdigest()

    @classmethod
    def hash_from_file(cls, path: pathlib.Path) -> str:
        file_hash = hashlib.md5()
        blocksize = 8192
        with open(path, "rb") as f:
            chunk = f.read(blocksize)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(blocksize)
        return file_hash.hexdigest()

    @staticmethod
    def get_examples() -> t.List[str]:
        return [TextMD5Signal.hash_from_str(s) for s in RawTextSignal.get_examples()]
