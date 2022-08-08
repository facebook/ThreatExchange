# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pytest
from pathlib import Path

try:
    import vpdq

    _DISABLED = False
except (ImportError, ModuleNotFoundError) as e:
    _DISABLED = True
else:
    from threatexchange.extensions.vpdq.vpdq import VPDQSignal
    from threatexchange.extensions.vpdq.vpdq_util import (
        vpdq_to_json,
        json_to_vpdq,
        read_file_to_hash,
        VPDQ_QUALITY_THRESHOLD,
        VPDQ_DISTANCE_THRESHOLD,
    )
    from threatexchange.extensions.vpdq.vpdq_brute_matcher import (
        match_VPDQ_hash_brute,
    )

VIDEO = "tmk/sample-videos/chair-20-sd-bar.mp4"
HASH = "python-threatexchange/threatexchange/extensions/vpdq/tests/test_hash.txt"
ROOTDIR = Path(__file__).parents[5]


@pytest.mark.skipif(_DISABLED, reason="vpdq not installed")
def test_vpdq_from_string_path():
    computed_hash = VPDQSignal.hash_from_file(ROOTDIR / VIDEO)
    expected_hash = read_file_to_hash(ROOTDIR / HASH)
    assert vpdq_to_json(json_to_vpdq(computed_hash)) == computed_hash
    res = match_VPDQ_hash_brute(
        json_to_vpdq(computed_hash),
        expected_hash,
        VPDQ_QUALITY_THRESHOLD,
        VPDQ_DISTANCE_THRESHOLD,
    )
    assert res.query_match_percent == 100
    assert res.compared_match_percent == 100
