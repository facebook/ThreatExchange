# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import typing as t
import vpdq_matcher
import vpdq_util
import os

SAMPLE = "/sample-hashes"


class TestVPDQFaiss(unittest.TestCase):
    def setUp(self):
        d = os.path.dirname(os.getcwd())
        sample_folder = d + SAMPLE
        self.index = vpdq_matcher.VPDQFlatHashIndex()
        self.test_videos = []
        id = 0
        for file in os.listdir(sample_folder):
            if file.endswith(".txt"):
                sample_file = f"{sample_folder}/{file}"
                cur = vpdq_util.read_file_to_hash(sample_file)
                self.index.add_single_video(cur, video_id=id)
                self.test_videos.append(cur)
                id += 1
        self.target_hash = self.test_videos[0]

    def assertEqualVPDQPercentMatchResults(self, result, expected):
        self.assertEqual(
            result[0],
            expected[0],
            "search results not of expected target match percentage",
        )
        self.assertEqual(
            result[1],
            expected[1],
            "search results not of expected target query percentage",
        )

    def test_VPDQ_Faiss_match_result(self):
        faiss_result = vpdq_matcher.match_VPDQ_FAISS(
            self.target_hash, self.index, 50, 31
        )
        brute_result = []
        for v in self.test_videos:
            brute_result.append(
                vpdq_matcher.match_VPDQ_hash_brute(self.target_hash, v, 50, 31)
            )
        for f in faiss_result:
            faiss_percent = f[1:3]
            video_id = f[0]
            self.assertEqualVPDQPercentMatchResults(
                faiss_percent, brute_result[video_id]
            )

    def test_VPDQ_Faiss_quality_filter(self):
        faiss_result = vpdq_matcher.match_VPDQ_FAISS(
            self.target_hash, self.index, 100, 31
        )
        brute_result = []
        for v in self.test_videos:
            brute_result.append(
                vpdq_matcher.match_VPDQ_hash_brute(self.target_hash, v, 100, 31)
            )
        for f in faiss_result:
            faiss_percent = f[1:3]
            video_id = f[0]
            self.assertEqualVPDQPercentMatchResults(
                faiss_percent, brute_result[video_id]
            )


if __name__ == "__main__":
    unittest.main()
