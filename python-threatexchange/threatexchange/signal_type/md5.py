#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the MD5 signal types.
"""

import hashlib
import pathlib
import typing as t

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent

from . import signal_base


class VideoMD5Signal(signal_base.SimpleSignalType, signal_base.BytesHasher):
    """
    Simple signal type for Video MD5s.

    Videos are quite expensive to process due to their large size. A simple
    matching algorithm is to just match against the file MD5, since
    transcoding is expensive enough that many platforms don't bother doing it.

    Even a single pixel changes will generate a new MD5 - consider formats
    that are capable of some notion of similarity, such as TMK+PDQF.
    """

    INDICATOR_TYPE = "VIDEO_HASH_MD5"

    @classmethod
    def get_content_types(self) -> t.List[t.Type[ContentType]]:
        return [VideoContent]

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
    def hash_from_bytes(self, bytes_: bytes) -> str:
        bytes_hash = hashlib.md5()
        bytes_hash.update(bytes_)
        return bytes_hash.hexdigest()

    @staticmethod
    def get_examples() -> t.List[str]:
        return ["cab08b36195edb1a1231d2d09fa450e0", "d41d8cd98f00b204e9800998ecf8427e"]


class PhotoMD5Signal(VideoMD5Signal):
    """
    Simple signal type for Photo MD5s.

    Unlike Videos, transcoding of photos is quite common. This should be
    a format of last resort, as the open source PDQ algorithm will usually
    have much higher recall without too much loss in precision.
    """

    INDICATOR_TYPE = "HASH_MD5"
    TYPE_TAG = "media_type_photo"

    @classmethod
    def get_content_types(self) -> t.List[t.Type[ContentType]]:
        return [PhotoContent]
