import time
import unittest
import datetime
import tempfile
import shutil
from threatexchange.timebuckets import TimeBucket


class TestTimeBuckets(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.sample = TimeBucket(
            datetime.timedelta(minutes=1), self.tempdir, "hasher", 1
        )

    def test_correct_file_storage(self):
        self.sample.add_record({"a": "b"})
        self.sample.add_record({"c": "d"})

        self.sample._addToFileSystem()
        numFiles = len(self.sample.getRecords())

        shutil.rmtree(self.tempdir)
        self.assertEqual(numFiles, 1, "Invalid number of files")
