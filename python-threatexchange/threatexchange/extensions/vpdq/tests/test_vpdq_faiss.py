# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pytest
import pickle
import random
from threatexchange.extensions.vpdq.vpdq_util import VpdqCompactFeature

from threatexchange.signal_type.index import IndexMatch

try:
    import vpdq

    _DISABLED = False
except (ImportError, ModuleNotFoundError) as e:
    _DISABLED = True
else:
    import typing as t
    from threatexchange.extensions.vpdq.vpdq_index import VPDQIndex, VPDQSimilarityInfo
    from threatexchange.extensions.vpdq.vpdq_util import (
        json_to_vpdq,
        prepare_vpdq_feature,
        VPDQ_QUALITY_THRESHOLD,
        vpdq_to_json,
        dedupe,
        quality_filter,
    )
    from threatexchange.extensions.vpdq.tests.utils import (
        get_random_vpdq_features,
        pdq_hashes_to_vpdq_features,
    )
    from threatexchange.extensions.vpdq.vpdq import VPDQSignal
    from threatexchange.tests.hashing.utils import (
        get_random_hash,
        get_similar_hash,
        get_zero_hash,
    )

pytestmark = pytest.mark.skipif(_DISABLED, reason="vpdq not installed")


def pdq_to_vpdq(hashes):
    return vpdq_to_json(
        [VpdqCompactFeature(h, 100, float(ts)) for ts, h in enumerate(hashes)]
    )


EXAMPLE_META_DATA = {"hash_type": "vpdq", "video_id": 5}
VIDEO1_META_DATA = object()
VIDEO2_META_DATA = object()
VIDEO3_META_DATA = object()
VIDEO4_META_DATA = object()
# Frames/features
F1 = get_similar_hash(get_zero_hash(), 16)
F2 = get_similar_hash(get_zero_hash(), 16 + (32 + 1))
F3 = get_similar_hash(get_zero_hash(), 16 + (32 + 1) * 2)
F4 = get_similar_hash(get_zero_hash(), 16 + (32 + 1) * 3)
# Groups
G1 = [get_similar_hash(F1, i) for i in range(0, 16)]
G2 = [get_similar_hash(F2, i) for i in range(0, 16)]
G3 = [get_similar_hash(F3, i) for i in range(0, 16)]

HASH = pdq_to_vpdq([F1, F2, F3, F4])
FEATURES = prepare_vpdq_feature(HASH, VPDQ_QUALITY_THRESHOLD)
# Three groups of hashes that are 128 hamming distance away from each other.
# The hashes match with each other within the group. And each group's hashes don't match.


def test_utils():
    example_hash = VPDQSignal.get_examples()[0]
    example_features = json_to_vpdq(example_hash)
    assert example_hash == vpdq_to_json(example_features)

    feature_size = len(example_features)
    assert len(dedupe(example_features)) == feature_size
    assert len(quality_filter(example_features, 50)) == feature_size
    assert len(quality_filter(example_features, 101)) == 0
    example_features.append(example_features[0])
    assert len(dedupe(example_features)) == feature_size

    frame_counts = 100
    features = get_random_vpdq_features(frame_counts)
    assert len(features) == frame_counts
    VPDQSignal.validate_signal_str(vpdq_to_json(features))
    pdq_hashes = [get_random_hash() for i in range(frame_counts)]
    VPDQSignal.validate_signal_str(
        vpdq_to_json(pdq_hashes_to_vpdq_features(pdq_hashes))
    )


def test_simple():
    index = VPDQIndex.build([[HASH, EXAMPLE_META_DATA]])
    assert index._entry_idx_to_features_and_entries[0][0] == FEATURES
    assert len(index._index_idx_to_vpdqHex_and_entry) == len(FEATURES)
    res = index.query(HASH)
    # A complete match to itself
    assert res[0] == IndexMatch(VPDQSimilarityInfo(100.0, 100.0), EXAMPLE_META_DATA)


def test_half_match():
    index = VPDQIndex.build([[HASH, EXAMPLE_META_DATA]], query_match_threshold_pct=0)
    half_hash = FEATURES[0 : int(len(FEATURES) / 2)]
    res = index.query(vpdq_to_json(half_hash))
    assert res[0] == IndexMatch(VPDQSimilarityInfo(100.0, 50.0), EXAMPLE_META_DATA)

    index = VPDQIndex.build(
        [[vpdq_to_json(half_hash), EXAMPLE_META_DATA]], query_match_threshold_pct=0
    )
    res = index.query(HASH)
    assert res[0] == IndexMatch(VPDQSimilarityInfo(50.0, 100.0), EXAMPLE_META_DATA)


def test_serialize():
    index = VPDQIndex.build([[HASH, EXAMPLE_META_DATA]])
    pickled_data = pickle.dumps(index)
    reconstructed_index = pickle.loads(pickled_data)
    res = reconstructed_index.query(HASH)
    assert res[0] == IndexMatch(VPDQSimilarityInfo(100.0, 100.0), EXAMPLE_META_DATA)


def test_empty_video_():
    empty_video = []
    video1 = pdq_hashes_to_vpdq_features(G1)

    index = VPDQIndex.build([[vpdq_to_json(video1), VIDEO1_META_DATA]])
    res = index.query(vpdq_to_json(empty_video))
    assert len(res) == 0
    with pytest.raises(ValueError):
        VPDQIndex.build([[vpdq_to_json(empty_video), VIDEO2_META_DATA]])


def test_empty_signal_str():
    empty_signal_str = ""
    video1 = pdq_hashes_to_vpdq_features(G1)
    index = VPDQIndex.build([[vpdq_to_json(video1), VIDEO1_META_DATA]])
    res = index.query(empty_signal_str)
    assert len(res) == 0
    with pytest.raises(ValueError):
        VPDQIndex.build([[vpdq_to_json(empty_signal_str), VIDEO2_META_DATA]])


def test_duplicate_hashes():
    index = VPDQIndex.build([[HASH, VIDEO1_META_DATA]])
    index.add(HASH, VIDEO2_META_DATA)
    res = index.query(HASH)
    # A complete match to itself
    assert res[0] == IndexMatch(VPDQSimilarityInfo(100.0, 100.0), VIDEO1_META_DATA)
    assert res[1] == IndexMatch(VPDQSimilarityInfo(100.0, 100.0), VIDEO2_META_DATA)


def test_no_match():
    video1 = pdq_hashes_to_vpdq_features(G1)
    video2 = pdq_hashes_to_vpdq_features(G2)

    index = VPDQIndex.build([[vpdq_to_json(video1), VIDEO1_META_DATA]])
    res = index.query(vpdq_to_json(video2))
    assert len(res) == 0

    index = VPDQIndex.build([[vpdq_to_json(video2), VIDEO2_META_DATA]])
    res = index.query(vpdq_to_json(video1))
    assert len(res) == 0


def test_no_match_with_zero_threshold():
    # Index should not return any non-match result even if threshold is zero
    video1 = pdq_hashes_to_vpdq_features(G1)
    video2 = pdq_hashes_to_vpdq_features(G2)
    index = VPDQIndex.build(
        [[vpdq_to_json(video1), VIDEO1_META_DATA]],
        query_match_threshold_pct=0,
        index_match_threshold_pct=0,
    )
    res = index.query(vpdq_to_json(video2))
    assert len(res) == 0


def test_match_below_and_above_80pct_query_threshold():
    # Video1 contains five out of ten frames that match with indexed video4 -> query percent 50% and filtered
    # Video2 contains eight out of ten frames that match with indexed video4 -> query percent 80% and return
    # Video3 contains nine out of ten frames that match with indexed video4 -> query percent 90% and return
    video1 = pdq_hashes_to_vpdq_features(
        random.sample(G1, 2) + random.sample(G2, 3) + random.sample(G3, 5)
    )
    video2 = pdq_hashes_to_vpdq_features(
        random.sample(G1, 1) + random.sample(G2, 1) + random.sample(G3, 8)
    )
    video3 = pdq_hashes_to_vpdq_features(random.sample(G1, 1) + random.sample(G3, 9))
    video4 = pdq_hashes_to_vpdq_features(random.sample(G3, 10))

    index = VPDQIndex.build(
        [[vpdq_to_json(video4), VIDEO4_META_DATA]],
        query_match_threshold_pct=80,
    )
    res = index.query(vpdq_to_json(video1))
    assert len(res) == 0

    res = index.query(vpdq_to_json(video2))
    assert res[0] == IndexMatch(VPDQSimilarityInfo(80.0, 100.0), VIDEO4_META_DATA)

    res = index.query(vpdq_to_json(video3))
    assert res[0] == IndexMatch(VPDQSimilarityInfo(90.0, 100.0), VIDEO4_META_DATA)


def test_match_below_and_above_80pct_index_threshold():
    # Indexed video1 contains five out of ten frames that match with quered video4 -> index percent 50% and filtered
    # Indexed video2 contains eight out of ten frames that match with quered video4 -> index percent 80% and return
    # Indexed video3 contains nine out of ten frames that match with quered video4 -> index percent 90% and return

    video1 = pdq_hashes_to_vpdq_features(
        random.sample(G1, 2) + random.sample(G2, 3) + random.sample(G3, 5)
    )
    video2 = pdq_hashes_to_vpdq_features(
        random.sample(G1, 1) + random.sample(G2, 1) + random.sample(G3, 8)
    )
    video3 = pdq_hashes_to_vpdq_features(random.sample(G1, 1) + random.sample(G3, 9))
    video4 = pdq_hashes_to_vpdq_features(random.sample(G3, 10))

    index = VPDQIndex.build(
        [[vpdq_to_json(video1), VIDEO1_META_DATA]],
        index_match_threshold_pct=80,
    )
    res = index.query(vpdq_to_json(video4))
    assert len(res) == 0

    index = VPDQIndex.build(
        [[vpdq_to_json(video2), VIDEO2_META_DATA]],
        index_match_threshold_pct=80,
    )
    res = index.query(vpdq_to_json(video4))
    assert res[0] == IndexMatch(VPDQSimilarityInfo(100.0, 80.0), VIDEO2_META_DATA)

    index = VPDQIndex.build(
        [[vpdq_to_json(video3), VIDEO3_META_DATA]],
        index_match_threshold_pct=80,
    )
    res = index.query(vpdq_to_json(video4))
    assert res[0] == IndexMatch(VPDQSimilarityInfo(100.0, 90.0), VIDEO3_META_DATA)


def test_matches():
    # Two videos (length 10) each with one unmatched frame. Query video2 with index built from video1 and vice versa.
    # Delete the unmatched frame from video1 and query. Then Delete the unmatched frame from video2 and query.
    video1 = pdq_hashes_to_vpdq_features(random.sample(G1, 9))
    video2 = pdq_hashes_to_vpdq_features(random.sample(G1, 9))
    video1.append(VpdqCompactFeature(get_similar_hash(get_zero_hash(), 255), 100, 10.0))
    video2.append(
        VpdqCompactFeature(get_similar_hash(video1[0].pdq_hex, 128), 100, 10.0)
    )
    index = VPDQIndex.build([[vpdq_to_json(video1), VIDEO1_META_DATA]])
    res = index.query(vpdq_to_json(video2))
    assert res[0] == IndexMatch(VPDQSimilarityInfo(90.0, 90.0), VIDEO1_META_DATA)

    index = VPDQIndex.build([[vpdq_to_json(video2), VIDEO2_META_DATA]])
    res = index.query(vpdq_to_json(video1))
    assert res[0] == IndexMatch(VPDQSimilarityInfo(90.0, 90.0), VIDEO2_META_DATA)

    del video1[-1]
    index = VPDQIndex.build([[vpdq_to_json(video1), VIDEO1_META_DATA]])
    res = index.query(vpdq_to_json(video2))
    assert res[0] == IndexMatch(VPDQSimilarityInfo(90.0, 100.0), VIDEO1_META_DATA)

    del video2[-1]
    index = VPDQIndex.build([[vpdq_to_json(video1), VIDEO1_META_DATA]])
    res = index.query(vpdq_to_json(video2))

    assert res[0] == IndexMatch(VPDQSimilarityInfo(100.0, 100.0), VIDEO1_META_DATA)


def test_duplicate_matches():
    # There are video1 (length 10) with one duplicate frame and Video2 (length 9) where matches all
    # unique frames in video1.The match percentage is (100, 100) because the duplicate one is deduped and not counted.
    video1 = pdq_hashes_to_vpdq_features(random.sample(G1, 9))
    video2 = pdq_hashes_to_vpdq_features(
        [get_similar_hash(h.pdq_hex, 31) for h in video1]
    )
    video1.append(VpdqCompactFeature(video1[8].pdq_hex, 10, 9.0))

    index = VPDQIndex.build([[vpdq_to_json(video1), VIDEO1_META_DATA]])
    res = index.query(vpdq_to_json(video2))
    assert res[0] == IndexMatch(VPDQSimilarityInfo(100.0, 100.0), VIDEO1_META_DATA)


def test_duplicate_video_matches():
    # There are video1 with 10 frames (from G1 and G2 evenly) and video2 which contains duplicated
    # first five frames in video2. Video3's frames are matched with video1's that belong to same group.
    video1 = pdq_hashes_to_vpdq_features(random.sample(G1, 5) + random.sample(G2, 5))
    video2 = video1[0:5]
    video3 = pdq_hashes_to_vpdq_features(random.sample(G1, 5) + random.sample(G2, 5))

    index = VPDQIndex(query_match_threshold_pct=0)
    index.add_all(
        [
            [vpdq_to_json(video1), VIDEO1_META_DATA],
            [vpdq_to_json(video2), VIDEO2_META_DATA],
        ]
    )
    res = index.query(vpdq_to_json(video3))
    assert res[0] == IndexMatch(VPDQSimilarityInfo(100.0, 100.0), VIDEO1_META_DATA)
    assert res[1] == IndexMatch(VPDQSimilarityInfo(50.0, 100.0), VIDEO2_META_DATA)
