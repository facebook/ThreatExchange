import vpdq
import typing as t
import pytest
import test_util
import os

SAMPLE_HASH_FOLDER = "/vpdq/sample-hashes"
SAMPLE_VIDEOS = "/tmk/sample-videos"
FFMPEG = "/usr/bin/ffmpeg"  # please customize according to your installation (but do not commit)
SECOND_PER_HASH = 1
DISTANCE_TOLERANCE = 31
QUALITY_TOLERANCE = 0


class TestVPDQHash:
    def test_VPDQ_hash(self):
        d = os.path.dirname(os.path.dirname(os.getcwd()))
        hash_folder = d + SAMPLE_HASH_FOLDER
        video_folder = d + SAMPLE_VIDEOS
        self.test_hashes = {}
        self.sample_hashes = {}

        for file in sorted(os.listdir(hash_folder)):
            if file.endswith(".txt"):
                hash_file = f"{hash_folder}/{file}"
                ret = test_util.read_file_to_hash(hash_file)
                name = os.path.splitext(file)[0]
                self.sample_hashes[name] = ret

        for file in sorted(os.listdir(video_folder)):
            if file.endswith(".mp4"):
                video_file = f"{video_folder}/{file}"
                ret = vpdq.computeHash(video_file, FFMPEG, False, SECOND_PER_HASH, 0, 0)
                name = os.path.splitext(file)[0]
                self.test_hashes[name] = ret

        for k in self.sample_hashes.keys():
            print("Comparing hash for video: " + k)
            hash1 = self.test_hashes[k]
            hash2 = self.sample_hashes[k]
            assert len(hash1) == len(hash2)
            for h1, h2 in zip(hash1, hash2):
                if h1.quality >= QUALITY_TOLERANCE and h2.quality >= QUALITY_TOLERANCE:
                    assert h1.hamming_distance(h2) < DISTANCE_TOLERANCE
                    assert h1.frame_number == h2.frame_number
