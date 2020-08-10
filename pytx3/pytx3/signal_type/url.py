#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the URL signal type.
"""

import typing as t

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import signal_base


class URLSignal(signal_base.SimpleSignalType, signal_base.StrMatcher):
    """
    Wrapper around URL links, such as https://github.com/
    """

    # TODO - Also handle URI indicator_type
    INDICATOR_TYPE = "RAW_URI"
    TYPE_TAG = "media_type_url"

    def match(self, content) -> t.List[signal_base.SignalMatch]:
        ret = []
        for word in content.split():
            found = self.state.get(word)
            if found:
                ret.append(
                    signal_base.SignalMatch(found.labels, found.first_descriptor_id)
                )
        return ret
