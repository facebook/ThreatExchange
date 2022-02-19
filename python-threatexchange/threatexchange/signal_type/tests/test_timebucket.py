import time
import unittest
import datetime
import tempfile
import shutil
from threatexchange.timebucketizer import TimeBucketizer


class TestTimeBuckets(unittest.TestCase):
    def test_correct_file_storage(self):

        with tempfile.TemporaryDirectory() as td:
            sample = TimeBucketizer(datetime.timedelta(minutes=1), td, "hasher", 1)
            sample.add_record({"a": "b"})
            sample.add_record({"c": "d"})
            sample._flush()
            numFiles = len(sample.get_records())
            self.assertEqual(numFiles, 1, "Invalid number of files")
