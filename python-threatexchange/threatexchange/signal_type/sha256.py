#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Wrapper around the SHA256 signal types.
"""

import hashlib
import pathlib
import re
import typing as t
import random

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.video import VideoContent
from threatexchange.exchanges.impl.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)
from threatexchange.signal_type import signal_base


class VideoSHA256Signal(
    signal_base.SimpleSignalType,
    signal_base.BytesHasher,
    HasFbThreatExchangeIndicatorType,
    signal_base.CanGenerateRandomSignal,
):
    """
    Simple signal type for Video SHA256s.

    SHA256 is a cryptographic hash function similar to MD5,
    but less prone to collisions.

    Two videos with the same SHA256 hash are almost certainly the same video pixel for pixel.
    """

    INDICATOR_TYPE = {"HASH_VIDEO_SHA256": None, "HASH_SHA256": "media_type_video"}

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [VideoContent]

    @classmethod
    def get_index_cls(cls) -> t.Type[signal_base.TrivialSignalTypeIndex]:
        return signal_base.TrivialSignalTypeIndex

    @classmethod
    def validate_signal_str(cls, signal_str: str) -> str:
        normalized = signal_str.strip().lower()
        if not re.match("^[0-9a-f]{64}$", normalized):
            raise ValueError(f"{signal_str!r} is not a valid SHA256 hash")
        return normalized

    @classmethod
    def hash_from_file(cls, path: pathlib.Path) -> str:
        file_hash = hashlib.sha256()
        blocksize = 8192
        with open(path, "rb") as f:
            chunk = f.read(blocksize)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(blocksize)
        return file_hash.hexdigest()

    @classmethod
    def hash_from_bytes(cls, bytes_: bytes) -> str:
        bytes_hash = hashlib.sha256()
        bytes_hash.update(bytes_)
        return bytes_hash.hexdigest()

    @classmethod
    def get_random_signal(cls) -> str:
        return f"{random.randrange(16**64):064x}"

    @staticmethod
    def get_examples() -> t.List[str]:
        return [
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "ba7816bf8f01cfe414134e77ca982da31a7b0e4a9e5a7a3a2a2a2a2a2a2a2a2a",
        ]
