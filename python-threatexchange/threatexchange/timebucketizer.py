import datetime
from datetime import timedelta
from inspect import _void

import os
from os import walk
from os.path import isfile, join

import json
from threading import Timer
from time import sleep
import time
from typing import List
import csv

import typing as t

# class JSONifiable:
#     def to_json(self) -> t.Dict:
#         raise NotImplementedError


class TimeBucketInstance:
    def to_csv(self) -> t.Dict:
        raise NotImplementedError


class TimeBucketizer(TimeBucketInstance):
    # TODO Make this generic, so we can have TimeBucket[Tuple[int, int]] or TimeBucket[MoreComplexObject].
    def __init__(
        self, bucket_width: datetime.timedelta, storage_path: str, type: str, id: str
    ):
        """
        Divides the day into 24h / bucket_width buckets. When add_record
        is called, based on current time, appends record to current bucket.
        Each bucket's data is stored as a serialized JSON file.
        Note that there may be multiple instances of TimeBucket writing to the
        same file system so add some uniqueness for this instance.

        Say your storage path is /var/data/threatexchange/timebuckets
        The file for current datetime (2022/02/08/20:49 UTC) for a bucket_width
        of 5 minutes should be "/var/data/threatexchange/timebuckets/<type>/2022/02/08/20:45/<unique_id>.json"

        The first <type> allows you to use the same storage folder for
        say hashes and matches.
        The second <unique_id> allows you to have multiple instances running
        (eg. multiple lambdas) and writing to the same file system.
        """

        if bucket_width < datetime.timedelta(seconds=60):
            raise Exception("Please ensure timedelta is atleast a minute long.")

        self.bucket_width = bucket_width
        # Add flag for BUCKET_WIDTH
        self.start, self.end = self._calculate_start(bucket_width)
        self.storage_path = storage_path
        self.id = id
        self.type = type

        self.buffer = []

    def _calculate_start(self, bucket_width):
        now = datetime.datetime.now()
        rounded = now - (now - datetime.datetime.min) % bucket_width
        return (rounded, rounded + self.bucket_width)

    def add_record(self, record) -> None:
        """
        Adds the record to the current bucket.
        """
        if len(self.buffer) > 100 or (self.end - self.start).days <= 0:
            self._flush()
        self.buffer.append(record)

    def get_records(self) -> List:
        """
        Used for testing. Returns a list of all filepathways found starting from the storage_path
        """
        directory_path = os.path.join(self.storage_path, self.type, "")

        list_of_pathways = [
            val
            for sublist in [
                [os.path.join(i[0], j) for j in i[2]] for i in os.walk(directory_path)
            ]
            for val in sublist
        ]

        return list_of_pathways

    def get_all_data_in_csv(self, directory_path):
        """
        Returns all the data in the csv files
        """
        with open(os.path.join(directory_path, str(self.id)) + ".csv") as f:
            data_count = sum(1 for _ in f)
        return data_count - 1

    def _flush(self) -> None:
        """
        Flushes the files currently stored onto the database
        """
        accurate_date = os.path.join(
            str(self.start.year),
            str(self.start.month),
            str(self.start.day),
            str(self.start.hour),
            str(self.start.minute),
        )

        file_name = str(self.id) + ".csv"
        directory_path = os.path.join(self.storage_path, self.type, accurate_date)
        file_pathway = os.path.join(directory_path, file_name)

        if not os.path.isdir(directory_path):
            os.makedirs(directory_path)

        with open(file_pathway, "a+", newline="") as outfile:
            writer = csv.writer(outfile)
            for val in self.buffer:
                writer.writerow([val])

        # Reset values
        self.start, self.end = self._calculate_start(self.bucket_width)
        self.buffer = []
