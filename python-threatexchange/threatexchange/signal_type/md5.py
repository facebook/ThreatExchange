#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the MD5 signal types.
"""

import hashlib
import pathlib
import re
import typing as t

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.video import VideoContent
from threatexchange.exchanges.impl.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)
from threatexchange.signal_type import signal_base


class VideoMD5Signal(
    signal_base.SimpleSignalType,
    signal_base.BytesHasher,
    HasFbThreatExchangeIndicatorType,
):
    """
    Simple signal type for Video MD5s.

    Videos are quite expensive to process due to their large size. A simple
    matching algorithm is to just match against the file MD5, since
    transcoding is expensive enough that many platforms don't bother doing it.

    Even a single pixel changes will generate a new MD5 - consider formats
    that are capable of some notion of similarity, such as TMK+PDQF.
    """

    INDICATOR_TYPE = {"HASH_VIDEO_MD5": None, "HASH_MD5": "media_type_video"}

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [VideoContent]

    @classmethod
    def get_index_cls(cls) -> t.Type[signal_base.TrivialSignalTypeIndex]:
        return signal_base.TrivialSignalTypeIndex

    @classmethod
    def validate_signal_str(cls, signal_str: str) -> str:
        normalized = signal_str.strip().lower()
        if not re.match("^[0-9a-f]{32}$", normalized):
            raise ValueError(f"{signal_str!r} is not a valid MD5 hash")
        return normalized

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

    @classmethod
    def hash_from_bytes(cls, bytes_: bytes) -> str:
        bytes_hash = hashlib.md5()
        bytes_hash.update(bytes_)
        return bytes_hash.hexdigest()

    @staticmethod
    def get_examples() -> t.List[str]:
        return ["cab08b36195edb1a1231d2d09fa450e0", "d41d8cd98f00b204e9800998ecf8427e"]
