import datetime
from datetime import timedelta

import os
from os import walk
from os.path import isfile, join

import json


class TimeBucket:
    # TODO Make this generic, so we can have TimeBucket[Tuple[int, int]] or TimeBucket[MoreComplexObject].
    def __init__(
        self, bucket_width: datetime.timedelta, storage_path: str, type: str, id: str
    ):
        # Divides the day into 24h / bucket_width buckets. When add_record
        # is called, based on current time, appends record to current bucket.
        # Each bucket's data is stored as a serialized JSON file.
        # Note that there may be multiple instances of TimeBucket writing to the
        # same file system so add some uniqueness for this instance.

        # Say your storage path is /var/data/threatexchange/timebuckets
        # The file for current datetime (2022/02/08/20:49 UTC) for a bucket_width
        # of 5 minutes should be "/var/data/threatexchange/timebuckets/<type>/2022/02/08/20:45/<unique_id>.json"

        # The first <type> allows you to use the same storage folder for
        # say hashes and matches.
        # The second <unique_id> allows you to have multiple instances running
        # (eg. multiple lambdas) and writing to the same file system.

        self.bucket_width = bucket_width
        self.start = self.calculateStart(bucket_width)
        self.storage_path = storage_path
        self.id = id
        self.type = type

        self.valuesToAdd = []

    def calculateStart(self, bucket_width):
        now = datetime.datetime.now()
        rounded = now - (now - datetime.datetime.min) % bucket_width
        return rounded

    def add_record(self, record):
        """
        Adds the record to the current bucket.
        """
        self.valuesToAdd.append(record)

    def getRecords(self):

        directoryPath = self.storage_path + "/" + self.type + "/"

        f = [
            val
            for sublist in [
                [os.path.join(i[0], j) for j in i[2]] for i in os.walk(directoryPath)
            ]
            for val in sublist
        ]

        return f

    def _addToFileSystem(self):

        value = self.calculateStart(self.bucket_width)
        print(self.storage_path)
        accurateDate = (
            str(value.year)
            + "/"
            + str(value.month)
            + "/"
            + str(value.day)
            + "/"
            + str(value.hour)
            + "/"
            + str(value.minute)
            + "/"
        )
        fileName = str(self.id) + ".txt"
        directoryPath = self.storage_path + "/hasher/" + accurateDate

        if not os.path.isdir(directoryPath):
            os.makedirs(directoryPath)

        with open(directoryPath + fileName, "a+") as outfile:
            for val in self.valuesToAdd:
                outfile.write(json.dumps(val))

        self.valuesToAdd = []


# x = TimeBucket(
#     datetime.timedelta(minutes=1), "/var/data/threatexchange/timebuckets", "hasher", 1
# )

# x.add_record({"a": "b"})
# x.add_record({"c": "d"})
# x.add_record({"e": "f"})
# x._addToFileSystem()
