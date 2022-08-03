# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest

from threatexchange.signal_type import (
    md5,
    raw_text,
    trend_query,
    url_md5,
    url,
)
from threatexchange.signal_type.pdq import signal
from threatexchange.signal_type.signal_base import TextHasher


class SignalTypeHashTest(unittest.TestCase):
    """
    Sanity check for signal type hashing methods.
    """

    # TODO - maybe make a metaclass for this to automatically detect?
    SIGNAL_TYPES_TO_TEST = [
        md5.VideoMD5Signal,
        signal.PdqSignal,
        raw_text.RawTextSignal,
        trend_query.TrendQuerySignal,
        url_md5.UrlMD5Signal,
        url.URLSignal,
    ]

    def test_signal_names_unique(self):
        seen = {}
        for s in self.SIGNAL_TYPES_TO_TEST:
            name = s.get_name()
            assert (
                name not in seen
            ), f"Two signal types share the same name: {s!r} and {seen[name]!r}"

    def test_signal_types_have_content(self):
        for s in self.SIGNAL_TYPES_TO_TEST:
            assert s.get_content_types(), "{s!r} has no content types"

    def test_str_hashers_have_impl(self):
        text_hashers = [
            s for s in self.SIGNAL_TYPES_TO_TEST if isinstance(s, TextHasher)
        ]
        for s in text_hashers:
            assert s.hash_from_str(
                "test string"
            ), "{s!r} produced no output from hasher"
