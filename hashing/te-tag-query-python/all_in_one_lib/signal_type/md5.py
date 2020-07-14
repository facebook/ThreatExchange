##!/usr/bin/env python

"""
Wrapper around the URL content type.
"""

import hashlib
import pathlib
import typing as t

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import base


class VideoMD5Signal(base.SimpleSignalType, base.FileMatcher):

    INDICATOR_TYPE = "HASH_MD5"
    TYPE_TAG = "media_type_video"

    def match_file(self, file: pathlib.Path) -> t.List[base.SignalMatch]:
        """Simple MD5 file match."""
        file_hash = hashlib.md5()
        blocksize = 8192
        with file.open('rb') as f:
            chunk = f.read(blocksize)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(blocksize)
        return self.match_hash(file_hash.hexdigest())


class PhotoMD5Signal(VideoMD5Signal):

    TYPE_TAG = "media_type_photo"
