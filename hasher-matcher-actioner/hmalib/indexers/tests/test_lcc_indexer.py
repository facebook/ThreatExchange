# Copyright (c) Meta Platforms, Inc. and affiliates.

import datetime
import tempfile
import unittest
from dataclasses import dataclass

from hmalib.common.models.pipeline import HashRecord
from hmalib.common.timebucketizer import CSViable, TimeBucketizer
from hmalib.indexers.lcc import LCCIndexer

from hmalib import metrics


class TestLCCIndexer(unittest.TestCase):
    def test(self):
        with tempfile.TemporaryDirectory() as td:
            tbi = TimeBucketizer(datetime.timedelta(minutes=1), td, "hasher", "2")
            tbi.add_record(
                HashRecord(
                    "55fc67a4e8d667d9668700c1920ff19055fc67a4e8d667d9668700c1920ff190",
                    "teststring",
                )
            )
            tbi.add_record(
                HashRecord(
                    "5c4474f0e17bb56d0d73cca24c77e0d75c4474f0e17bb56d0d73cca24c77e0d7",
                    "teststring",
                )
            )
            tbi.force_flush()
            test_class = LCCIndexer()

            test_index = test_class.build_index_from_last_24h(
                tbi.type, tbi.storage_path, tbi.bucket_width
            )

            test_class.override_recent_index(test_index, tbi.type, td, tbi.bucket_width)
            print(test_class.get_recent_index(td, tbi.type))

        assert True
