# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from cmath import sin
import json
import pytest
from pathlib import Path
import pickle

try:
    import vpdq as _

    _DISABLED = False
except (ImportError, ModuleNotFoundError) as e:
    _DISABLED = True
else:
    import typing as t
    from threatexchange.extensions.vpdq.vpdq_index import VPDQIndex
    from threatexchange.extensions.vpdq.vpdq_util import (
        prepare_vpdq_feature,
        json_to_vpdq,
        vpdq_to_json,
        VPDQ_QUALITY_THRESHOLD,
    )
    from threatexchange.extensions.vpdq.video_vpdq import VideoVPDQSignal

    from threatexchange.signal_type.index import (
        VPDQIndexMatch,
    )

pytestmark = pytest.mark.skipif(_DISABLED, reason="vpdq not installed")

if not _DISABLED:
    EXAMPLE_META_DATA = {"name": "example_video"}
    hash = VideoVPDQSignal.get_examples()[0]
    features = prepare_vpdq_feature(hash, VPDQ_QUALITY_THRESHOLD)


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


def compare_match_result(res1, res2) -> bool:
    return (
        res1.compared_match_percent == res2.compared_match_percent
        and res1.query_match_percent == res2.query_match_percent
        and res1.metadata == res2.metadata
        and res1.distance == res2.distance
    )
