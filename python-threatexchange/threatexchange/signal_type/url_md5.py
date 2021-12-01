#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the URL MD5 signal types.
"""

import hashlib

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import signal_base
from .. import common


class UrlMD5Signal(signal_base.SimpleSignalType, signal_base.StrHasher):
    """
    Simple signal type for URL MD5s.
    """

    INDICATOR_TYPE = "HASH_URL_MD5"
    TYPE_TAG = "media_type_url"

    @classmethod
    def hash_from_str(cls, url: str) -> str:
        encoded_url = common.normalize_url(url)
        url_hash = hashlib.md5(encoded_url)
        return url_hash.hexdigest()
