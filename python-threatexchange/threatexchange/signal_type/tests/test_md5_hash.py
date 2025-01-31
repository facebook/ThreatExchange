# Copyright (c) Meta Platforms, Inc. and affiliates.

import pathlib
import pytest
from threatexchange.signal_type.md5 import VideoMD5Signal

TEST_FILE = pathlib.Path(__file__).parent.parent.parent.parent.joinpath(
    "data", "sample-b.jpg"
)


def test_can_hash_simple_files():
    """
    Test that the VideoMD5Signal produces the expected hash.
    """
    with open(TEST_FILE, "rb") as f:
        file_content = f.read()

    expected_hash = "d35c785545392755e7e4164457657269"
    computed_hash = VideoMD5Signal.hash_from_bytes(file_content)
    assert computed_hash == expected_hash, "MD5 hash does not match"
