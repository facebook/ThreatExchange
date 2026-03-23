# Copyright (c) Meta Platforms, Inc. and affiliates.

import pathlib
import pytest
from threatexchange.signal_type.sha256 import VideoSHA256Signal

TEST_FILE = pathlib.Path(__file__).parent.parent.parent.parent.joinpath(
    "data", "sample-b.jpg"
)


def test_can_hash_simple_files():
    """
    Test that the VideoSHA256Signal produces the expected hash.
    """
    with open(TEST_FILE, "rb") as f:
        file_content = f.read()

    expected_hash = (
        "b5b0799616df52d475a3968dc7e54f1d0724c912244ffa6175bc786375dd7298"
    )
    computed_hash = VideoSHA256Signal.hash_from_bytes(file_content)
    assert computed_hash == expected_hash, "SHA256 hash does not match"
