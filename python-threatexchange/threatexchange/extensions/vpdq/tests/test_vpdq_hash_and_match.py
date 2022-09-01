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
        VpdqCompactFeature,
        VPDQ_QUALITY_THRESHOLD,
        VPDQ_DISTANCE_THRESHOLD,
    )
    from threatexchange.extensions.vpdq.vpdq_brute_matcher import (
        match_VPDQ_hash_brute,
    )

VIDEO = "tmk/sample-videos/chair-20-sd-bar.mp4"
ROOTDIR = Path(__file__).parents[5]


@pytest.mark.skipif(_DISABLED, reason="vpdq not installed")
def test_vpdq_from_string_path():
    computed_hash = VPDQSignal.hash_from_file(ROOTDIR / VIDEO)
    expected_hash = [
        VpdqCompactFeature(h, 100, float(i))
        for i, h in enumerate(
            (
                "e42926b9cb58d261383b699f0ff2e1076fe6183dff4986d82ca36da48034fc54",
                "4ce949b11f1035e2f2eb0a5e76f68716870e70f97bd91d1049a3dbe1d164b454",
                "643c8f9e5f0eb6866886355a4a4bdbe38343a4e924b969b41d321ba33a85f55e",
                "02b456d6bd4b6d695aa51772cdb8fa1df0ced12ea64b82f106e53d1b7e0b8050",
                "e64c35684e8d8926cc96324b66b9c999d92c37566669999b9bb166e464cbdd11",
                "46d86a5cc1ac1787f2b5cb895833c6a59e07b37ca60524ccaf1b69af9b2d9053",
                "c5f2ada74d0649858d6f1d26adace8fcd4b98d1938d131fca75a9611b41332d2",
                "093455b85518971cb48dad0f2b464a7552b3049345a905e904db2fde6ff66ff9",
                "e25339b25ecca73c5b1c84650a4b17a6afd21eac3d12fa14f00ff81bf03ce178",
                "8834b4ce2ca75b4d964e2526096f02cc27a63fa7be42fc16f83f486b487e4b78",
                "b26d60de1b62b499e0bc83680f8c3b25f0fae3b6c72b6e397c3414710e634d4e",
                "b506c921960c6d24e70705071c3b64e6e1a7ced61cf639ea199e1e345b726f6e",
                "93457d84eb67a4c33a63f4ca9307361b7161e709cc1578c129c93cbc94b0df5e",
                "419d81cc6926e1c6cfe67ae6e1e6c25b9af03349e7057641acc98c1c96196f5e",
                "64368799091de307e9855b6ee1e6c3e61ff633618701c64378c91c9d9499d75a",
                "256393c7dbcc7cb93665831385dae732586338abf439c89683c6a3e1d129b552",
                "cad9719334499e3dcb3361233744e9cc519b2a89d7e8a21734f679696921d556",
                "e0d8834b1f0bebf1e362e4ad0bac1b5efc9a81cb6ee97c34812793a19285e554",
                "9d4a35397761e5511559f178e5660f06dd4ec1b97f99b952122326e9e269d114",
                "792efd6e85e31b812a5162f95ea63a5622d60bb99d70a2564aab5de99549a154",
                "efc4c1861a3326f148d9de093bb9c1b65d46acab80dcdf42895e223d7f61c554",
            )
        )
    ]
    assert vpdq_to_json(json_to_vpdq(computed_hash)) == computed_hash
    res = match_VPDQ_hash_brute(
        json_to_vpdq(computed_hash),
        expected_hash,
        VPDQ_QUALITY_THRESHOLD,
        VPDQ_DISTANCE_THRESHOLD,
    )
    assert res.query_match_percent == 100
    assert res.compared_match_percent == 100
