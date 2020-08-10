#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the Photo PDQ signal type.
"""

import typing as t

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import signal_base


class PdqSignal(signal_base.SimpleSignalType):
    """
    PDQ is an open source photo similarity algorithm.

    Unlike MD5s, which are sensitive to single pixel differences, PDQ has
    a concept of "distance" and can detect when content is visually similar.
    This property tends to make it much more effective at finding images that
    a human would claim are the same, but also opens the door for false
    positives.

    Which distance to use can differ based on the type of content being
    searched for. While the PDQ documentation suggests certain thresholds,
    they can sometimes vary depending on what you are comparing against.
    """

    INDICATOR_TYPE = "HASH_PDQ"
    TYPE_TAG = "media_type_photo"

    # TODO at least hash distance functionality
