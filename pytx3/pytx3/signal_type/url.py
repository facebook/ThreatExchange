#!/usr/bin/env python

"""
Wrapper around the URL signal type.
"""

import typing as t

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import base


class URLSignal(base.SimpleSignalType, base.StrMatcher):
    """
    Wrapper around URL links, such as https://github.com/
    """

    # TODO - Also handle URI indicator_type
    INDICATOR_TYPE = "RAW_URI"
    TYPE_TAG = "media_type_url"

    def match(self, content) -> t.List[base.SignalMatch]:
        ret = []
        for word in content.split():
            found = self.state.get(word)
            if found:
                ret.append(base.SignalMatch(found.labels, found.first_descriptor_id))
        return ret
