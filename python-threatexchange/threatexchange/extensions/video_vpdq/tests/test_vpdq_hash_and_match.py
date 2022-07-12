# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import unittest
import test_util
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parents[1]))
try:
    import vpdq as _

    _DISABLED = False
except ImportError:
    _DISABLED = True
else:
    from threatexchange.extensions.video_vpdq.video_vpdq import VideoVPDQSignal
    from vpdq_util import vpdq_to_json, TARGET_MATCH_PERCENT, QUERY_MATCH_PERCENT

VIDEO = "test_video.mp4"
HASH = "test_hash.txt"
WORKDIR = Path.cwd()


@unittest.skipIf(_DISABLED, "vpdq not installed")
class VPDQHasherModuleUnitTest(unittest.TestCase):
    def test_vpdq_from_string_path(self):
        computed_hash = VideoVPDQSignal.hash_from_str(str(WORKDIR / VIDEO))
        expected_hash = test_util.read_file_to_hash(str(WORKDIR / HASH))
        res, _ = VideoVPDQSignal.compare_hash(
            computed_hash, vpdq_to_json(expected_hash)
        )
        self.assertEqual(getattr(res, TARGET_MATCH_PERCENT), 100)
        self.assertEqual(getattr(res, QUERY_MATCH_PERCENT), 100)
