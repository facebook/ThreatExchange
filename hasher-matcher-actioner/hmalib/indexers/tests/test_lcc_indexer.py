import datetime
import tempfile
import unittest
from dataclasses import dataclass

from hmalib.common.models.pipeline import HashRecord
from hmalib.common.timebucketizer import CSViable, TimeBucketizer
from hmalib.indexers.lcc import LCCIndexer

# python -m py.test hmalib/indexers/tests/test_lcc_indexer.py::TestLCCIndexer::test


@dataclass(eq=True)
class SampleCSViableClass(CSViable):
    """
    Example class used for testing purposes.
    """

    def __init__(self):
        self.a = "a"
        self.b = "b"

    def to_csv(self):
        return [self.a, self.b]

    def from_csv(self, value):
        return SampleCSViableClass()


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
            test_index = test_class.build_index_from_last_24h(tbi)
            print(
                test_index.query(
                    "19055fc67a4e8d667d9668700c1920ff19005fc67a4e8d667d9668700c1920ff"
                )
            )
            # should return a list with non-zero length
            self.assertEqual(3, 4)
        # print("Hello", testClass)
