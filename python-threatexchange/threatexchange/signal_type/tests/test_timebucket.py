import time
import unittest
import datetime
import tempfile
import shutil
from threatexchange.timebucketizer import CSViable, TimeBucketizer
from freezegun import freeze_time
import os
from os import walk


class TestTimeBuckets(unittest.TestCase):
    class testA(CSViable):
        def __init__(self):
            self.a = "a"
            self.b = "b"

        def to_csv(self):
            return [self.a, self.b]

    def test_correct_file_storage(self):

        with tempfile.TemporaryDirectory() as td:
            sample = TimeBucketizer(datetime.timedelta(minutes=1), td, "hasher", "1")
            sample.add_record(self.testA())
            sample.add_record(self.testA())
            sample._flush()
            numFiles = len(sample.get_records())
            self.assertEqual(numFiles, 1, "Invalid number of files")

    def test_correct_file_content(self):
        with tempfile.TemporaryDirectory() as td:
            initial_datetime = datetime.datetime(
                year=2012, month=8, day=13, hour=14, minute=4
            )
            other_datetime = datetime.datetime(
                year=2012, month=8, day=13, hour=14, minute=5
            )
            with freeze_time(initial_datetime) as frozen_datetime:
                sample = TimeBucketizer(
                    datetime.timedelta(minutes=1), td, "hasher", "2"
                )
                sample.add_record(self.testA())
                sample.add_record(self.testA())
                frozen_datetime.move_to(other_datetime)
                sample.add_record(self.testA())
                fileContent = sample.get_file_contents(
                    os.path.join(td, "hasher", "2012", "8", "13", "14", "4", "2.csv")
                )

                to_compare = [self.testA().to_csv()] * 2
                self.assertEqual(fileContent, to_compare, "File content does not match")

    def test_multiple_files_and_content(self):
        with tempfile.TemporaryDirectory() as td:
            initial_datetime = datetime.datetime(
                year=2012, month=8, day=13, hour=14, minute=4
            )
            with freeze_time(initial_datetime) as frozen_datetime:
                sample = TimeBucketizer(
                    datetime.timedelta(minutes=1), td, "hasher", "3"
                )

                for _ in range(5):
                    for _ in range(3):
                        sample.add_record(self.testA())
                    frozen_datetime.tick(delta=datetime.timedelta(minutes=1))
                fileContent = []
                sample.add_record(self.testA())
                for i in range(5):
                    fileContent.extend(
                        sample.get_file_contents(
                            os.path.join(
                                td,
                                "hasher",
                                "2012",
                                "8",
                                "13",
                                "14",
                                str(4 + i),
                                "3.csv",
                            )
                        )
                    )

                to_compare = [self.testA().to_csv()] * 5 * 3
                self.assertEqual(fileContent, to_compare, "Invalid data")

    @freeze_time("2012-08-13 14:04:00")
    def test_buffer_overload(self):
        with tempfile.TemporaryDirectory() as td:
            sample = TimeBucketizer(datetime.timedelta(minutes=1), td, "hasher", "4")
            for _ in range(102):
                sample.add_record(self.testA())

            fileContent = sample.get_file_contents(
                os.path.join(td, "hasher", "2012", "8", "13", "14", "4", "4.csv")
            )
            to_compare = [self.testA().to_csv()] * 100
            self.assertEqual(
                fileContent,
                to_compare,
                "Buffer overload did not write the file and reset the buffer.",
            )
