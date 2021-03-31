# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import os

from threatexchange.content_type import meta
from threatexchange.signal_type.signal_base import FileHasher, StrHasher
from pathlib import Path


class TestHashFrom(unittest.TestCase):
    """
    Signal Type has a weird inheritance structure the error around which are easy to
    miss before run time. If a SignalType is a FileHasher/StrHasher it should be able to
    take the corresponding content medium without throwing.
    """

    def test_file_hashers_have_impl(self):
        signal_types = [s() for s in meta.get_all_signal_types()]
        file_hashers = [s for s in signal_types if issubclass(type(s), FileHasher)]
        for file_hasher in file_hashers:
            file_hasher.hash_from_file(
                Path(os.path.dirname(__file__) + "/../../../tests/data/b.jpg")
            )

    def test_str_hashers_have_impl(self):
        signal_types = [s() for s in meta.get_all_signal_types()]
        str_hashers = [s for s in signal_types if issubclass(type(s), StrHasher)]
        for str_hasher in str_hashers:
            str_hasher.hash_from_str("test string")

    def test_supports_pickling(self):
        pass
