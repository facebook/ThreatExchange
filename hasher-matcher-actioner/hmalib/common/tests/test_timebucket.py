# Copyright (c) Meta Platforms, Inc. and affiliates.
import datetime
import os
import random
import string
import tempfile
import typing as t
import unittest
from dataclasses import dataclass

from freezegun import freeze_time
from hmalib.common.models.pipeline import HashRecord
from hmalib.common.timebucketizer import CSViable, TimeBucketizer


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

    @classmethod
    def from_csv(cls, value: t.List[str]):
        return SampleCSViableClass()


class TestTimeBuckets(unittest.TestCase):
    def get_file_count(self, directory_path):
        file_count = 0
        for _, _, files in os.walk(directory_path):
            file_count += len(files)
        return file_count

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
                sample.add_record(SampleCSViableClass())
                sample.add_record(SampleCSViableClass())
                frozen_datetime.move_to(other_datetime)
                sample.add_record(SampleCSViableClass())

                fileContent = sample.get_records(
                    initial_datetime,
                    other_datetime,
                    "hasher",
                    td,
                    datetime.timedelta(minutes=1),
                    SampleCSViableClass,
                )

                to_compare = [SampleCSViableClass()] * 2
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
                        sample.add_record(SampleCSViableClass())
                    frozen_datetime.tick(delta=datetime.timedelta(minutes=1))
                sample.add_record(SampleCSViableClass())

                fileContent = sample.get_records(
                    initial_datetime,
                    datetime.datetime.now(),
                    "hasher",
                    td,
                    datetime.timedelta(minutes=1),
                    SampleCSViableClass,
                )

                to_compare = [SampleCSViableClass()] * 5 * 3

                self.assertEqual(fileContent, to_compare, "Invalid data")

    @freeze_time("2012-08-13 14:04:00")
    def test_buffer_overload(self):
        with tempfile.TemporaryDirectory() as td:
            sample = TimeBucketizer(datetime.timedelta(minutes=1), td, "hasher", "4")
            for _ in range(3201):
                sample.add_record(SampleCSViableClass())

            fileContent = sample.get_records(
                datetime.datetime.now(),
                datetime.datetime.now(),
                "hasher",
                td,
                datetime.timedelta(minutes=1),
                SampleCSViableClass,
            )

            to_compare = [SampleCSViableClass()] * 3200

            self.assertEqual(
                fileContent,
                to_compare,
                "Buffer overload, did not write the file and reset the buffer.",
            )

    def test_force_flush(self):
        with tempfile.TemporaryDirectory() as td:
            sample = TimeBucketizer(datetime.timedelta(minutes=1), td, "hasher", "4")
            for _ in range(5):
                sample.add_record(SampleCSViableClass())

            sample.force_flush()

            fileContent = sample.get_records(
                datetime.datetime.now(),
                datetime.datetime.now(),
                "hasher",
                td,
                datetime.timedelta(minutes=1),
                SampleCSViableClass,
            )

            to_compare = [SampleCSViableClass()] * 5

            self.assertEqual(
                fileContent,
                to_compare,
                "Destroy method did not flush the remaining files stored in the buffer",
            )

    def test_destroy_empty_buffer(self):
        with tempfile.TemporaryDirectory() as td:
            sample = TimeBucketizer(datetime.timedelta(minutes=1), td, "hasher", "4")
            sample.force_flush()

            fileContent = sample.get_records(
                datetime.datetime.now(),
                datetime.datetime.now(),
                "hasher",
                td,
                datetime.timedelta(minutes=1),
                SampleCSViableClass,
            )

            self.assertEqual(
                fileContent,
                [],
                "Destroy method should not have executed as the buffer is empty",
            )

    @freeze_time("2012-08-13 14:04:00")
    def test_squash_content(self):
        with tempfile.TemporaryDirectory() as td:
            with freeze_time(datetime.datetime.now()) as frozen_datetime:
                VALUE_1 = 5
                VALUE_2 = 10
                VALUE_3 = 3
                expected_records = []
                for i in range(VALUE_1):
                    for i in range(VALUE_2):
                        sample = TimeBucketizer(
                            datetime.timedelta(minutes=1), td, "hasher", str(i)
                        )
                        for i in range(VALUE_3):
                            content = "".join(
                                random.choice(string.ascii_lowercase) for _ in range(10)
                            )
                            new_record = HashRecord(content, str(i))
                            sample.add_record(new_record)
                            expected_records.append(new_record)
                        sample.force_flush()
                    frozen_datetime.tick(delta=datetime.timedelta(minutes=1))

                frozen_datetime.tick(delta=datetime.timedelta(minutes=1))
                frozen_datetime.tick(delta=datetime.timedelta(minutes=1))
                frozen_datetime.tick(delta=datetime.timedelta(minutes=1))

                file_count_prev = self.get_file_count(td)

                TimeBucketizer.squash_content(
                    "hasher",
                    td,
                    datetime.timedelta(minutes=1),
                    datetime.datetime.now() - datetime.timedelta(days=1),
                    datetime.datetime.now() - datetime.timedelta(minutes=2),
                )

                records = TimeBucketizer.get_records(
                    datetime.datetime.now() - datetime.timedelta(minutes=10),
                    datetime.datetime.now(),
                    "hasher",
                    td,
                    datetime.timedelta(minutes=1),
                    HashRecord,
                )

                now = datetime.datetime(2012, 8, 13, 14, 4, 0)

                file_count = self.get_file_count(td)

                self.assertEqual(len(records), VALUE_1 * VALUE_2 * VALUE_3)
                self.assertCountEqual(records, expected_records)
                self.assertEqual(file_count_prev, VALUE_1 * VALUE_2)
                self.assertEqual(file_count, VALUE_1)
