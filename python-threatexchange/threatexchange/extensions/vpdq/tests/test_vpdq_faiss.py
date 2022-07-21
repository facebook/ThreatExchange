# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

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
        vpdq_to_json,
        read_file_to_hash,
        prepare_vpdq_feature,
        VPDQ_QUALITY_THRESHOLD,
    )
    from threatexchange.extensions.vpdq.video_vpdq import VideoVPDQSignal

    from threatexchange.signal_type.index import (
        VPDQIndexMatch,
    )

ROOTDIR = Path(__file__).parents[5]
hash = VideoVPDQSignal.get_examples()[0]
features = prepare_vpdq_feature(hash, VPDQ_QUALITY_THRESHOLD)
example_meta_data = {"name": "example_video"}


@pytest.mark.skipif(_DISABLED, reason="vpdq not installed")
def test_simple():
    index = VPDQIndex.build([[hash, example_meta_data]])
    assert index.entry_idx_to_features_and_entires[0][0] == features
    assert len(index.index_idx_to_vpdqFrame) == len(features)
    res = index.query(hash)
    # A complete match to itself
    assert compare_match_result(res[0], VPDQIndexMatch(-1, 100, 100, example_meta_data))


def test_serialize():
    index = VPDQIndex.build([[hash, example_meta_data]])
    pickled_data = pickle.dumps(index)
    reconstructed_index = pickle.loads(pickled_data)
    res = reconstructed_index.query(hash)
    assert compare_match_result(res[0], VPDQIndexMatch(-1, 100, 100, example_meta_data))


def compare_match_result(res1: VPDQIndexMatch, res2: VPDQIndexMatch) -> bool:
    return (
        res1.compared_match_percent == res2.compared_match_percent
        and res1.query_match_percent == res2.query_match_percent
        and res1.metadata == res2.metadata
        and res1.distance == res2.distance
    )
