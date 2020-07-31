#!/usr/bin/env python

"""
Wrapper around the raw text signal type.
"""

import typing as t
import pathlib

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import base


class RawTextSignal(base.SimpleSignalType, base.StrMatcher):
    """
    Raw text signal is the same as raw text content: the exact text content.

    Unlike other formats like photos or videos, it is difficult to come
    up with non-reversable hashes of text information which are also effective
    at detecting similar content.
    """

    INDICATOR_TYPE = "DEBUG_STRING"
    TYPE_TAG = "media_type_text"

    def match(self, content: str) -> t.List[base.SignalMatch]:
        return self.match_hash(content)
