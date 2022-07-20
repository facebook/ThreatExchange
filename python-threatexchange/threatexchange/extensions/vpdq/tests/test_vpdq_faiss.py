# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pytest
from pathlib import Path

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
    )

HASH = "python-threatexchange/threatexchange/extensions/vpdq/tests/test_hash.txt"
ROOTDIR = Path(__file__).parents[5]


@pytest.mark.skipif(_DISABLED, reason="vpdq not installed")
def test_simple():
    hash = read_file_to_hash(ROOTDIR / HASH)
    index = VPDQIndex()
    index.add(vpdq_to_json(hash), ["test_video"])
    res = index.query_raw_result(vpdq_to_json(hash[0:1]))
    assert len(res[hash[0].hex]) == 18
    res = index.query(vpdq_to_json(hash[0:1]))
    assert res[0].query_match_percent == 100
