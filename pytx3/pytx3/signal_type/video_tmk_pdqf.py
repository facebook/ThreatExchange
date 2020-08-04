#!/usr/bin/env python

"""
Wrapper around the TMK+PDQF signal type.
"""

import typing as t

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import base


class VideoTmkPdqfSignal(base.SimpleSignalType):
    """
    TMK+PDQF is an open-source, constant length hash for videos.

    Video MD5s are a constant length hash, which makes them simple to
    implement a lookup against an index of hashes, but are sensitive to minor
    changes in the video content (even a single pixel changed changes the MD5).
    TMK+PDQF has a notion of "distance" which can be used to tell when content
    is similar, if not identical.
    """

    INDICATOR_TYPE = "HASH_TMK"
    TYPE_TAG = "media_type_long_hash_video"

    # TODO at least hash distance functionality
