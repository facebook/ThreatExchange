# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the vpdq signal type.
"""

import vpdq
from .vpdq_util import json_to_vpdq, vpdq_to_json
from .vpdq_brute_hasher import match_VPDQ_hash_brute
import pathlib
import typing as t
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.video import VideoContent
import re
from threatexchange.signal_type import signal_base
from threatexchange.signal_type.pdq import PdqSignal


class VideoVPDQSignal(signal_base.SimpleSignalType, signal_base.FileHasher):
    """
    Simple signal type for video using VPDQ.
    VPDQ signal_str is the json serialization from a list of VPDQ features
    The json serialization will converts the the list of VPDQ features to list of json objects
    where frame_number is the key:
    {(frame_number)
        0: {
            "quality": 100,
            "hash": Hash256,
            "timestamp": 0.0
            },

        1: {
            "quality": 100,
            "hash": Hash256,
            "timestamp": 0.1
            },
            ...
    }
    Read about VPDQ at https://github.com/facebook/ThreatExchange/tree/main/vpdq
    """

    INDICATOR_TYPE = "HASH_VIDEO_VPDQ"
    VPDQ_CONFIDENT_DISTANCE_THRESHOLD = 31
    VPDQ_CONFIDENT_QUALITY_THRESHOLD = 50
    VPDQ_CONFIDENT_MATCH_THRESHOLD = 80.0

    @classmethod
    def get_content_types(self) -> t.List[t.Type[ContentType]]:
        return [VideoContent]

    @classmethod
    def validate_signal_str(cls, signal_str: str) -> str:
        """
        VPDQ feature contains quality(int), frame_number(int), hash(Hash256), hex(hex_str of the hash) and timestamp(double)
        Hex is a hexadecimal string contains 64 hexidecimal characters
        frame_number is an non-negative integer
        quality is a 0-100 integer(inclusive)
        timestamp(sec, round to 3 decimal) is the start time of the frame for the VPDQ feature
        """
        vpdq_hashes = json_to_vpdq(signal_str)
        last_frame_number = -1
        for hash in vpdq_hashes:
            if not re.match("^[0-9a-f]{64}$", hash.hex):
                raise ValueError("invalid VPDQ hash")
            if hash.quality < 0 or hash.quality > 100:
                raise ValueError("invalid VPDQ hash")
            if hash.frame_number < 0 or hash.frame_number <= last_frame_number:
                last_frame_number = hash.frame_number
                raise ValueError("invalid VPDQ hash")
        return signal_str

    @classmethod
    def hash_from_file(cls, path: pathlib.Path) -> str:
        vpdq_hashes = vpdq.computeHash(str(path))
        return vpdq_to_json(vpdq_hashes)

    @classmethod
    def compare_hash(
        cls, hash1: str, hash2: str, distance_threshold: t.Optional[int] = None
    ) -> signal_base.HashComparisonResult:
        """ "If the max of the two match percentages is over 80% match percent with 31 distance threshold, it's a match."""
        vpdq_hash1 = json_to_vpdq(hash1)
        vpdq_hash2 = json_to_vpdq(hash2)
        match_percent = match_VPDQ_hash_brute(
            vpdq_hash1,
            vpdq_hash2,
            cls.VPDQ_CONFIDENT_DISTANCE_THRESHOLD,
            cls.VPDQ_CONFIDENT_QUALITY_THRESHOLD,
        )
        match = (
            max(match_percent.query_match_percent, match_percent.target_match_percent)
            >= cls.VPDQ_CONFIDENT_MATCH_THRESHOLD
        )
        return signal_base.HashComparisonResult.from_bool(match)

    @staticmethod
    def get_examples() -> t.List[str]:
        frame_number = 0
        timestamp = 0.0
        quality = 100
        VPDQ_features = []
        for pdq_hash in PdqSignal.get_examples():
            VPDQ_features.append(
                vpdq.VpdqFeature(
                    quality, frame_number, vpdq.str_to_hash(pdq_hash), timestamp
                )
            )
            timestamp += 1.0
            frame_number += 1
        return [vpdq_to_json(VPDQ_features)]
