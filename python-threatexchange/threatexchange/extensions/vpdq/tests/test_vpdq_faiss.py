# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import pytest
from pathlib import Path
import pickle

try:
    import vpdq

    _DISABLED = False
except (ImportError, ModuleNotFoundError) as e:
    _DISABLED = True
else:
    import typing as t
    from threatexchange.extensions.vpdq.vpdq_index import VPDQIndex
    from threatexchange.extensions.vpdq.vpdq_util import (
        json_to_vpdq,
        prepare_vpdq_feature,
        VPDQ_QUALITY_THRESHOLD,
        vpdq_to_json,
        dedupe,
        quality_filter,
    )
    from threatexchange.extensions.vpdq.tests.utils import (
        get_random_VPDQs,
        pdq_hashes_to_VPDQ_features,
    )
    from threatexchange.extensions.vpdq.video_vpdq import VideoVPDQSignal
    from tests.hashing.utils import get_random_hash, get_similar_hash, get_zero_hash
    from threatexchange.signal_type.index import (
        VPDQIndexMatch,
    )

pytestmark = pytest.mark.skipif(_DISABLED, reason="vpdq not installed")

if not _DISABLED:
    EXAMPLE_META_DATA = {"name": "example_video"}
    hash = VideoVPDQSignal.get_examples()[0]
    features = prepare_vpdq_feature(hash, VPDQ_QUALITY_THRESHOLD)


def test_utils():
    example_hash = VideoVPDQSignal.get_examples()[0]
    example_features = json_to_vpdq(example_hash)
    assert example_hash == vpdq_to_json(example_features)

    feature_size = len(example_features)
    assert len(dedupe(example_features)) == feature_size
    assert len(quality_filter(example_features, 50)) == feature_size
    assert len(quality_filter(example_features, 101)) == 0
    example_features.append(example_features[0])
    assert len(dedupe(example_features)) == feature_size

    frame_counts = 100
    features = get_random_VPDQs(frame_counts)
    assert len(features) == frame_counts
    VideoVPDQSignal.validate_signal_str(vpdq_to_json(features))
    pdq_hashes = [get_random_hash() for i in range(frame_counts)]
    VideoVPDQSignal.validate_signal_str(
        vpdq_to_json(pdq_hashes_to_VPDQ_features(pdq_hashes))
    )


def test_simple():
    index = VPDQIndex.build([[hash, EXAMPLE_META_DATA]])
    assert index._entry_idx_to_features_and_entires[0][0] == features
    assert len(index._index_idx_to_vpdqHex_and_entry) == len(features)
    res = index.query(hash)
    # A complete match to itself
    assert compare_match_result(
        res[0], VPDQIndexMatch(100, 100, 100, EXAMPLE_META_DATA)
    )


def test_half_match():
    index = VPDQIndex.build([[hash, EXAMPLE_META_DATA]])
    half_hash = features[0 : int(len(features) / 2)]
    res = index.query(vpdq_to_json(half_hash))
    assert compare_match_result(res[0], VPDQIndexMatch(100, 100, 50, EXAMPLE_META_DATA))
    index = VPDQIndex.build([[vpdq_to_json(half_hash), EXAMPLE_META_DATA]])
    res = index.query(hash)
    assert compare_match_result(res[0], VPDQIndexMatch(100, 50, 100, EXAMPLE_META_DATA))


def test_serialize():
    index = VPDQIndex.build([[hash, EXAMPLE_META_DATA]])
    pickled_data = pickle.dumps(index)
    reconstructed_index = pickle.loads(pickled_data)
    res = reconstructed_index.query(hash)
    assert compare_match_result(
        res[0], VPDQIndexMatch(100, 100, 100, EXAMPLE_META_DATA)
    )


def test_duplicate_hashes():
    index = VPDQIndex.build([[hash, {"name": "video1"}]])
    index.add(hash, {"name": "video2"})
    res = index.query(hash)
    # A complete match to itself
    assert compare_match_result(
        res[0], VPDQIndexMatch(100, 100, 100, {"name": "video1"})
    )
    assert compare_match_result(
        res[1], VPDQIndexMatch(100, 100, 100, {"name": "video2"})
    )


def test_no_match():
    video1 = pdq_hashes_to_VPDQ_features(
        [get_similar_hash(get_zero_hash(), 50) for i in range(10)]
    )
    video2 = pdq_hashes_to_VPDQ_features(
        [get_similar_hash(get_zero_hash(), 82) for i in range(10)]
    )

    index = VPDQIndex.build([[vpdq_to_json(video1), {"name": "video1"}]])
    res = index.query(vpdq_to_json(video2))
    assert len(res) == 0

    index = VPDQIndex.build([[vpdq_to_json(video2), {"name": "video2"}]])
    res = index.query(vpdq_to_json(video1))
    assert len(res) == 0


def test_matches():
    video1 = pdq_hashes_to_VPDQ_features(
        [get_similar_hash(get_zero_hash(), 5) for i in range(9)]
    )
    video2 = pdq_hashes_to_VPDQ_features(
        [get_similar_hash(hash.hex, 20) for hash in video1]
    )
    video1.append(
        vpdq.VpdqFeature(
            100, 10, vpdq.str_to_hash(get_similar_hash(get_zero_hash(), 255)), 10
        )
    )
    video2.append(
        vpdq.VpdqFeature(
            100, 10, vpdq.str_to_hash(get_similar_hash(video1[0].hex, 128)), 10
        )
    )
    index = VPDQIndex.build([[vpdq_to_json(video1), {"name": "video1"}]])
    res = index.query(vpdq_to_json(video2))
    assert compare_match_result(res[0], VPDQIndexMatch(90, 90, 90, {"name": "video1"}))

    index = VPDQIndex.build([[vpdq_to_json(video2), {"name": "video2"}]])
    res = index.query(vpdq_to_json(video1))
    assert compare_match_result(res[0], VPDQIndexMatch(90, 90, 90, {"name": "video2"}))

    del video1[-1]
    index = VPDQIndex.build([[vpdq_to_json(video1), {"name": "video1"}]])
    res = index.query(vpdq_to_json(video2))
    assert compare_match_result(
        res[0], VPDQIndexMatch(100, 90, 100, {"name": "video1"})
    )

    del video2[-1]
    index = VPDQIndex.build([[vpdq_to_json(video1), {"name": "video1"}]])
    res = index.query(vpdq_to_json(video2))

    assert compare_match_result(
        res[0], VPDQIndexMatch(100, 100, 100, {"name": "video1"})
    )


def test_duplicate_matches():
    video1 = pdq_hashes_to_VPDQ_features(
        [get_similar_hash(get_zero_hash(), 5) for i in range(9)]
    )
    video2 = pdq_hashes_to_VPDQ_features(
        [get_similar_hash(hash.hex, 20) for hash in video1]
    )
    video1.append(vpdq.VpdqFeature(100, 9, vpdq.str_to_hash(video1[8].hex), 9))

    index = VPDQIndex.build([[vpdq_to_json(video1), {"name": "video1"}]])
    res = index.query(vpdq_to_json(video2))
    assert compare_match_result(
        res[0], VPDQIndexMatch(100, 100, 100, {"name": "video1"})
    )


def test_duplicate_video_matches():
    max_hash = get_similar_hash(get_zero_hash(), 256)
    video1 = pdq_hashes_to_VPDQ_features([get_zero_hash(), max_hash])
    video2 = video1[0:1]
    video3 = pdq_hashes_to_VPDQ_features(
        [get_similar_hash(hash.hex, 31) for hash in video1]
    )

    index = VPDQIndex()
    index.add_all(
        [
            [vpdq_to_json(video1), {"name": "video1"}],
            [vpdq_to_json(video2), {"name": "video2"}],
        ]
    )
    res = index.query(vpdq_to_json(video3))
    assert compare_match_result(
        res[0], VPDQIndexMatch(100, 100, 100, {"name": "video1"})
    )
    assert compare_match_result(
        res[1], VPDQIndexMatch(100, 50, 100, {"name": "video2"})
    )


def compare_match_result(res1, res2) -> bool:
    return (
        res1.compared_match_percent == res2.compared_match_percent
        and res1.query_match_percent == res2.query_match_percent
        and res1.metadata == res2.metadata
        and res1.distance == res2.distance
    )
