# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pickle
import time
import typing as t
from dataclasses import dataclass
from datetime import datetime, timedelta

from hmalib.common.logging import get_logger
from threatexchange.signal_type.pdq_index import PDQIndex
from threatexchange.signal_type.timebucketizer import TimeBucketizer

starttime = time.time()
logger = get_logger(__name__)

# parameters of get_records
# def get_records(
#         since: datetime.datetime,
# until: datetime.datetime,
# type: str,
# storage_path: str,
# bucket_width: datetime.timedelta,
# type_class: t.Type[CSViable],
# ):

class LCCIndexer:
    @classmethod
    def get_recent_index(cls) -> PDQIndex:
        """Get the most recent index."""

    # find some way to access most recent index in file structure
    # indexObjPath = path of index with latest creation time (should already be sorted by time in file structure)
    # file = open(indexObjPath,"r")
    # latest_index = pickle.load(file)
    # file.close()
    # return latest_index

    @classmethod
    def build_index_from_last_24h(cls) -> void:
        """Create an index"""
        d = timedelta(days=1)

        past_day_content = TimeBucketizer.get_records(
            (datetime.now() - d),
            datetime.now(),
            "hasher",
            "/tmp/makethisdirectory/ ",
            d,
            SampleCSViableClass,
        )
        now = datetime.now()

        testIndex = PDQIndex.build(past_day_content)
        # variable name with creation time, index type, time delta value
        indexObj = {testIndex, datetime.now(), PDQIndex, d}
        # write_path = open(indexpath,"w")
        pickle.dump(indexObj, write_path)
        # example file structure
        # "/var/data/threatexchange/LCCIndexes/<hash_type>/2022-02-08-20-45-<pickle-name>.pickle"
        # os.listdirs, check if this returns sorted list of files
