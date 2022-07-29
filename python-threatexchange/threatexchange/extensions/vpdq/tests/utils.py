# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import vpdq
import typing as t
from threatexchange.extensions.vpdq.vpdq_index import VPDQIndex
from threatexchange.tests.hashing.utils import get_random_hash


def get_random_VPDQs(
    frame_count: int, seconds_per_frame: float = 1.0, quality: int = 100
) -> t.List[vpdq.VpdqFeature]:
    """Return a List which contains frame_count random VPDQ features with same quality and each feature's time stamp differs by seconds_per_frame"""
    return [
        vpdq.VpdqFeature(
            quality, i, vpdq.str_to_hash(get_random_hash()), i * seconds_per_frame
        )
        for i in range(frame_count)
    ]


def pdq_hashes_to_VPDQ_features(
    pdq_hashes: t.List[str], seconds_per_frame: float = 1.0, quality: int = 100
) -> t.List[vpdq.VpdqFeature]:
    """Return a List of VPDQ features generated from pdq_hashes with same quality and each feature's time stamp differs by seconds_per_frame"""
    return [
        vpdq.VpdqFeature(quality, i, vpdq.str_to_hash(pdq_hash), i * seconds_per_frame)
        for i, pdq_hash in enumerate(pdq_hashes)
    ]
