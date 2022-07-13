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
    Read about VPDQ at https://github.com/facebook/ThreatExchange/tree/main/vpdq
    """

    INDICATOR_TYPE = "HASH_VIDEO_VPDQ"
    VPDQ_CONFIDENT_DISTANCE_THRESHOLD = 31
    VPDQ_CONFIDENT_QUALITY_THRESHOLD = 50

    @classmethod
    def get_content_types(self) -> t.List[t.Type[ContentType]]:
        return [VideoContent]

    @classmethod
    def validate_signal_str(cls, signal_str: str) -> str:
        """VPDQ signal_str is a list of VPDQ features"""
        """VPDQ feature contains quality(int), frame_number(int), hash(Hash256), hex(str) and timestamp(double)"""
        """Hex is hexadecimal string contains 64 hexidecimal characters."""
        """frame_number is non-negative integer."""
        """quality is a 0-100 interger(inclusive)."""
        """timestamp is the start time of the frame for the VPDQ feature in second."""
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
        vpdq_hash1 = json_to_vpdq(hash1)
        vpdq_hash2 = json_to_vpdq(hash2)
        match_percent = match_VPDQ_hash_brute(
            vpdq_hash1,
            vpdq_hash2,
            cls.VPDQ_CONFIDENT_QUALITY_THRESHOLD,
            cls.VPDQ_CONFIDENT_QUALITY_THRESHOLD,
        )
        return signal_base.HashComparisonResult(match_percent, distance_threshold)  # type: ignore #video vpdq should return two percentages instead of just true or false

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
            timestamp += 0.1
            frame_number += 1
        return [vpdq_to_json(VPDQ_features)]
