# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import pathlib

from threatexchange.signal_type.md5 import VideoMD5Signal

TEST_FILE = pathlib.Path(__file__).parent.parent.parent.parent.joinpath(
    "data", "sample-b.jpg"
)


class VideoMD5SignalTestCase(unittest.TestCase):
    def setUp(self):
        self.a_file = open(TEST_FILE, "rb")

    def tearDown(self):
        self.a_file.close()

    def test_can_hash_simple_files(self):
        assert "d35c785545392755e7e4164457657269" == VideoMD5Signal.hash_from_bytes(
            self.a_file.read()
        ), "MD5 hash does not match"
