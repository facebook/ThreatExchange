# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import csv
import datetime
import os
import typing as t
import uuid
import random
import string
from dataclasses import dataclass, field


MAX_BUFFER_SIZE = 3200
SECONDS_PER_DAY = 86400
SECONDS_PER_MINUTE = 60


Self = t.TypeVar("Self", bound="CSViable")


class CSViable:
    """
    Interface of methods that must be implemented to run TimeBucketizer. It is used to guarantee safe parsing data in and out of CSV files
    """

    def to_csv(self) -> t.List[t.Union[str, int]]:
        raise NotImplementedError

    @classmethod
    def from_csv(cls: t.Type[Self], value: t.List[str]) -> Self:
        raise NotImplementedError


T = t.TypeVar("T", bound=CSViable)


class TimeBucketizer(t.Generic[T]):
    def __init__(
        self,
        bucket_width: datetime.timedelta,
        storage_path: str,
        type: str,
        id: str,
        buffer_size: int = MAX_BUFFER_SIZE,
    ):
        """
        Divides the day into 24h / bucket_width buckets. When add_record
        is called, based on current time, appends record to current bucket.
        Each bucket's data is stored as a serialized CSV file.
        Note that there may be multiple instances of TimeBucket writing to the
        same file system so add some uniqueness for this instance.

        Say your storage path is /var/data/threatexchange/timebuckets
        The file for current datetime (2022/02/08/20:49 UTC) for a bucket_width
        of 5 minutes should be "/var/data/threatexchange/timebuckets/<type>/2022/02/08/20/45/<unique_id>.csv"

        The first <type> allows you to use the same storage folder for
        say hashes and matches.
        The second <unique_id> allows you to have multiple instances running
        (eg. multiple lambdas) and writing to the same file system.
        """

        if bucket_width.total_seconds() < 60 or bucket_width.total_seconds() % 60 != 0:
            raise Exception("Please ensure timedelta is atleast a minute long.")

        if SECONDS_PER_DAY % bucket_width.total_seconds() != 0:
            raise Exception(
                "Time Delta must be equally divisible into buckets based on a 24 hour clock"
            )

        self.bucket_width = bucket_width
        self.start, self.end = self._calculate_bucket_endpoints(
            datetime.datetime.now(), bucket_width
        )
        self.storage_path = storage_path
        self.id = id
        self.type = type

        self.buffer_size = buffer_size
        self.buffer: t.List[T] = []

    @staticmethod
    def _generate_path(storage_path: str, type: str, date: datetime.datetime):
        return os.path.join(
            storage_path,
            type,
            str(date.year),
            str(date.month),
            str(date.day),
            str(date.hour),
            str(date.minute),
        )

    @staticmethod
    def _calculate_bucket_endpoints(
        time: datetime.datetime, bucket_width: datetime.timedelta
    ):
        now = time
        rounded = now - (now - datetime.datetime.min) % bucket_width
        return (rounded, rounded + bucket_width)

    def add_record(self, record: T) -> None:
        """
        Adds the record to the current bucket.
        """
        if len(self.buffer) >= MAX_BUFFER_SIZE or self.end <= datetime.datetime.now():
            self._flush()
        self.buffer.append(record)

    def force_flush(self) -> None:
        """
        Used to trigger a force flush of remaining data stored inside buffer
        """
        if not len(self.buffer):
            return
        self._flush()

    def _flush(self) -> None:
        """
        Flushes the current data onto storage source
        """

        file_name = str(self.id) + ".csv"
        directory_path = self._generate_path(self.storage_path, self.type, self.start)
        file_path = os.path.join(directory_path, file_name)

        if not os.path.isdir(directory_path):
            os.makedirs(directory_path)

        # Opening in append mode because it's possible we have to write to the same file multiple times with preexisting data
        # newline is overridden to prevent spaces in the csv file between sections
        with open(file_path, "a+", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerows(map(lambda x: x.to_csv(), self.buffer))

        self.start, self.end = self._calculate_bucket_endpoints(
            datetime.datetime.now(), self.bucket_width
        )
        self.buffer = []

    @staticmethod
    def get_records(
        since: datetime.datetime,
        until: datetime.datetime,
        type: str,
        storage_path: str,
        bucket_width: datetime.timedelta,
        type_class: t.Type[CSViable],
    ):
        """
        Returns the data of all csv files stored between the interval of 'since' to 'until'.
        Uses the provided type_class.from_csv() method to return record data as a list of type_class instances.
        """

        since_nearest = TimeBucketizer._calculate_bucket_endpoints(since, bucket_width)[
            0
        ]
        until_nearest = TimeBucketizer._calculate_bucket_endpoints(until, bucket_width)[
            1
        ]

        content_list = []
        file_list = []
        while since_nearest <= until_nearest:

            directory_path = TimeBucketizer._generate_path(
                storage_path, type, since_nearest
            )

            if os.path.isdir(directory_path):
                file_list.extend(
                    [
                        os.path.join(directory_path, file)
                        for file in os.listdir(directory_path)
                        if os.path.isfile(os.path.join(directory_path, file))
                    ]
                )
            since_nearest += bucket_width

        for file in file_list:
            with open(file, "r") as my_file:
                content_list.extend(list(map(type_class.from_csv, csv.reader(my_file))))

        return content_list

    @staticmethod
    def squash_content(
        location: datetime.datetime,
        type: str,
        storage_path: str,
        bucket_width: datetime.timedelta,
        date_to: datetime.timedelta = datetime.timedelta(days=1),
    ):

        if bucket_width > date_to:
            return

        until_nearest = TimeBucketizer._calculate_bucket_endpoints(
            location, bucket_width
        )[1]

        since_nearest = TimeBucketizer._calculate_bucket_endpoints(
            until_nearest - date_to, bucket_width
        )[0]

        while until_nearest > since_nearest:

            directory_path = TimeBucketizer._generate_path(
                storage_path, type, until_nearest
            )

            if os.path.isdir(directory_path):
                file_list = []
                for file in os.listdir(directory_path):
                    file_path = os.path.join(directory_path, file)
                    if file.startswith("squash"):
                        return
                    elif os.path.isfile(file_path):
                        file_list.append(file_path)

                with open(
                    os.path.join(directory_path, "squash" + str(uuid.uuid1())) + ".csv",
                    "w",
                ) as new_file:
                    for file in file_list:
                        with open(file, "r") as reader:
                            new_file.write(reader.read())

                        os.remove(file)

            until_nearest -= bucket_width
