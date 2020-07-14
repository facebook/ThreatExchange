##!/usr/bin/env python

"""
Wrapper around the URL content type.
"""

import typing as t

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import base


class VideoTmkPdqfSignal(base.SimpleSignalType):

    INDICATOR_TYPE = "HASH_TMK"
    TYPE_TAG = "media_type_long_hash_video"

    # TODO at least hash distance functionality
