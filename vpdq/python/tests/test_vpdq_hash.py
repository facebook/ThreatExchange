# Copyright (c) Meta Platforms, Inc. and affiliates.
import vpdq
import pytest
import test_util
import os
from pathlib import Path
import sys

SAMPLE_HASH_FOLDER = Path("vpdq/sample-hashes")
SAMPLE_VIDEOS = Path("tmk/sample-videos")
DISTANCE_TOLERANCE = 31
QUALITY_TOLERANCE = 50
TEST_FILES = [
    "chair-19-sd-bar",
    "chair-20-sd-bar",
    "chair-22-sd-grey-bar",
    "chair-22-sd-sepia-bar",
    "chair-22-with-large-logo-bar",
    "chair-22-with-small-logo-bar",
    "chair-orig-22-fhd-no-bar",
    "chair-orig-22-hd-no-bar",
    "chair-orig-22-sd-bar",
    "doorknob-hd-no-bar",
    "pattern-hd-no-bar",
    "pattern-longer-no-bar",
    "pattern-sd-grey-bar",
    "pattern-sd-with-large-logo-bar",
    "pattern-sd-with-small-logo-bar",
]

project_dir = Path(__file__).parents[3]
hash_folder = project_dir / SAMPLE_HASH_FOLDER
video_folder = project_dir / SAMPLE_VIDEOS
test_hashes = {}
sample_hashes = {}


def test_vpdq_utils():
    sample = Path(f"{hash_folder}/{TEST_FILES[0]}.txt")
    assert sample.is_file()
    ret = test_util.read_file_to_hash(sample)
    with open(sample, "r") as file:
        lines = file.readlines()
    for line, feature in zip(lines, ret):
        line = line.strip()
        content = line.split(",")
        hex_hash = content[2]
        assert vpdq.str_to_hash(hex_hash) == feature.hash
        assert vpdq.hash_to_hex(feature.hash) == hex_hash


def test_error_checking():
    video_file = Path(f"{video_folder}/{TEST_FILES[0]}.mp4")
    with pytest.raises(ValueError, match="Seconds_per_hash must be non-negative"):
        vpdq.computeHash(input_video_filename=video_file, seconds_per_hash=-1)

    with pytest.raises(ValueError, match="Downsample_width must be non-negative"):
        vpdq.computeHash(input_video_filename=video_file, downsample_width=-1)

    with pytest.raises(ValueError, match="Downsample_height must be non-negative"):
        vpdq.computeHash(input_video_filename=video_file, downsample_height=-1)

    with pytest.raises(ValueError, match="Input_video_filename doesn't exist"):
        vpdq.computeHash(input_video_filename="nonexisting")


def test_compare_hashes():
    """This regression test is creating hashes from sample videos and compare them with the provided hashes line by line.
    Two VPDQ features are considered the same if each line of the hashes are within DISTANCE_TOLERANCE.
    For hashes that have a quality lower than QUALITY_TOLERANCE, the test will skip them for comoparing.
    """

    for file in TEST_FILES:
        hash_file = Path(f"{hash_folder}/{file}.txt")
        assert hash_file.is_file()
        ret = test_util.read_file_to_hash(hash_file)
        assert ret is not None
        sample_hashes[file] = ret

        video_file = Path(f"{video_folder}/{file}.mp4")
        assert video_file.is_file()
        ret = vpdq.computeHash(input_video_filename=video_file, seconds_per_hash=0)
        assert ret is not None
        test_hashes[file] = ret

        print("Comparing hash for video:", file)
        hash1 = test_hashes[file]
        hash2 = sample_hashes[file]
        assert len(hash1) == len(hash2)
        for h1, h2 in zip(hash1, hash2):
            if h1.quality >= QUALITY_TOLERANCE and h2.quality >= QUALITY_TOLERANCE:
                assert h1.hamming_distance(h2) < DISTANCE_TOLERANCE
                assert h1.frame_number == h2.frame_number
