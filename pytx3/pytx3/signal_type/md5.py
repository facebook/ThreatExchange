#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the MD5 signal types.
"""

import hashlib
import pathlib
import typing as t

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import signal_base


class VideoMD5Signal(signal_base.SimpleSignalType, signal_base.FileMatcher):
    """
    Simple signal type for Video MD5s.

    Videos are quite expensive to process due to their large size. A simple
    matching algorithm is to just match against the file MD5, since
    transcoding is expensive enough that many platforms don't bother doing it.

    Even a single pixel changes will generate a new MD5 - consider formats
    that are capable of some notion of similarity, such as TMK+PDQF.
    """

    INDICATOR_TYPE = "HASH_MD5"
    TYPE_TAG = "media_type_video"

    def match_file(self, file: pathlib.Path) -> t.List[signal_base.SignalMatch]:
        """Simple MD5 file match."""
        file_hash = hashlib.md5()
        blocksize = 8192
        with file.open("rb") as f:
            chunk = f.read(blocksize)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(blocksize)
        return self.match_hash(file_hash.hexdigest())


class PhotoMD5Signal(VideoMD5Signal):
    """
    Simple signal type for Photo MD5s.

    Unlike Videos, transcoding of photos is quite common. This should be
    a format of last resort, as the open source PDQ algorithm will usually
    have much higher recall without too much loss in precision.
    """

    TYPE_TAG = "media_type_photo"
