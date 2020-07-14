##!/usr/bin/env python

"""
Wrapper around the raw text content type.
"""

import typing as t
import pathlib

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import base


class RawTextSignal(base.SimpleSignalType, base.StrMatcher):

    INDICATOR_TYPE = "DEBUG_STRING"
    TYPE_TAG = "media_type_text"

    def match(self, content: str) -> t.List[base.SignalMatch]:
        return self.match_hash(content)
