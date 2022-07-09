# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import vpdq
import pytest
import test_util
import os
from pathlib import Path
import sys

SAMPLE_HASH_FOLDER = Path("vpdq/sample-hashes")
SAMPLE_VIDEOS = Path("tmk/sample-videos")
DISTANCE_TOLERANCE = 10
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


class TestVPDQHash:
    def test_compare_hashes(self):
        """This regression test is creating hashes from sample videos and compare them with the provided hashes line by line.
        Two VPDQ features are considered the same if each line of the hashes are within DISTANCE_TOLERANCE.
        For hashes that have a quality lower than QUALITY_TOLERANCE, the test will skip them for comoparing.
        """
        project_dir = Path(__file__).parents[3]
        hash_folder = project_dir / SAMPLE_HASH_FOLDER
        video_folder = project_dir / SAMPLE_VIDEOS
        test_hashes = {}
        sample_hashes = {}

        for file in TEST_FILES:
            hash_file = Path(f"{hash_folder}/{file}.txt")
            assert hash_file.is_file()
            ret = test_util.read_file_to_hash(hash_file)
            assert ret is not None
            sample_hashes[file] = ret

            video_file = Path(f"{video_folder}/{file}.mp4")
            assert video_file.is_file()
            ret = vpdq.computeHash(
                input_video_filename=str(video_file),
            )
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
