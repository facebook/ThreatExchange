# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pytest
from pathlib import Path

try:
    import vpdq as _

    _DISABLED = False
except (ImportError, ModuleNotFoundError) as e:
    _DISABLED = True
else:
    from threatexchange.extensions.video_vpdq.video_vpdq import VideoVPDQSignal
    from threatexchange.extensions.video_vpdq.vpdq_util import (
        vpdq_to_json,
        json_to_vpdq,
        read_file_to_hash,
        dedupe,
        quality_filter,
    )
    from threatexchange.extensions.video_vpdq.vpdq_brute_matcher import (
        match_VPDQ_hash_brute,
    )

VIDEO = "tmk/sample-videos/chair-20-sd-bar.mp4"
HASH = "python-threatexchange/threatexchange/extensions/video_vpdq/tests/test_hash.txt"
ROOTDIR = Path(__file__).parents[5]


@pytest.mark.skipif(_DISABLED, reason="vpdq not installed")
class TestVPDQHasherMatcher:
    def test_vpdq_utils(self):
        example_hash = VideoVPDQSignal.get_examples()[0]
        example_features = json_to_vpdq(example_hash)
        feature_size = len(example_features)
        assert len(dedupe(example_features)) == feature_size
        assert len(quality_filter(example_features, 50)) == feature_size
        assert len(quality_filter(example_features, 101)) == 0
        example_features.append(example_features[0])
        assert len(dedupe(example_features)) == feature_size

    def test_vpdq_from_string_path(self):
        computed_hash = VideoVPDQSignal.hash_from_file(ROOTDIR / VIDEO)
        expected_hash = read_file_to_hash(ROOTDIR / HASH)
        assert vpdq_to_json(json_to_vpdq(computed_hash)) == computed_hash
        res = match_VPDQ_hash_brute(
            json_to_vpdq(computed_hash),
            expected_hash,
            VideoVPDQSignal.VPDQ_CONFIDENT_QUALITY_THRESHOLD,
            VideoVPDQSignal.VPDQ_CONFIDENT_DISTANCE_THRESHOLD,
        )
        assert res.query_match_percent == 100
        assert res.compared_match_percent == 100
