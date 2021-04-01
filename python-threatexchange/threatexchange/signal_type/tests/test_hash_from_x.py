# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import tempfile
from PIL import Image


from threatexchange.content_type import meta
from threatexchange.signal_type.signal_base import FileHasher, StrHasher
from pathlib import Path


class SignalTypeHashTest(unittest.TestCase):
    """
    If a SignalType is a FileHasher/StrHasher it should be able to
    take the corresponding content medium without throwing.
    """

    def test_file_hashers_have_impl(self):
        signal_types = [s() for s in meta.get_all_signal_types()]
        file_hashers = [s for s in signal_types if isinstance(s, FileHasher)]
        fp = tempfile.NamedTemporaryFile(suffix=".jpg")
        image = Image.new("RGB", size=(50, 50), color=(155, 0, 0))
        image.save(fp, "jpeg")
        for file_hasher in file_hashers:
            file_hasher.hash_from_file(fp.name)

    def test_str_hashers_have_impl(self):
        signal_types = [s() for s in meta.get_all_signal_types()]
        str_hashers = [s for s in signal_types if isinstance(s, StrHasher)]
        for str_hasher in str_hashers:
            str_hasher.hash_from_str("test string")
