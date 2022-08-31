# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import typing as t
from threatexchange.extensions.vpdq.vpdq_util import VpdqCompactFeature
from threatexchange.tests.hashing.utils import get_random_hash


def get_random_vpdq_features(
    frame_count: int, seconds_per_frame: float = 1.0, quality: int = 100
) -> t.List[VpdqCompactFeature]:
    """Return a List which contains frame_count random VPDQ features with same quality and each feature's time stamp differs by seconds_per_frame"""
    return pdq_hashes_to_vpdq_features(
        [get_random_hash() for _ in range(frame_count)], seconds_per_frame, quality
    )


def pdq_hashes_to_vpdq_features(
    pdq_hashes: t.List[str], seconds_per_frame: float = 1.0, quality: int = 100
) -> t.List[VpdqCompactFeature]:
    """Return a List of VPDQ features generated from pdq_hashes with same quality and each feature's time stamp differs by seconds_per_frame"""
    return [
        VpdqCompactFeature(pdq_hash, quality, i * seconds_per_frame)
        for i, pdq_hash in enumerate(pdq_hashes)
    ]
