# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import glob
import os.path
import pickle
import time
import typing as t
from dataclasses import dataclass
from datetime import datetime, timedelta

from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.signal_type.pdq_index import PDQIndex

from hmalib.common.logging import get_logger
from hmalib.common.models.pipeline import HashRecord
from hmalib.common.timebucketizer import TimeBucketizer

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
    def get_recent_index(cls, storage_path) -> PDQIndex:
        """Get the most recent index."""
        os.listdir(storage_path)[0]
        file_type = r"\*csv"
        files = glob.glob(storage_path + file_type)
        latest_index = max(files, key=os.path.getctime)
        return latest_index

    # find some way to access most recent index in file structure
    # indexObjPath = path of index with latest creation time (should already be sorted by time in file structure)
    # file = open(indexObjPath,"r")
    # latest_index = pickle.load(file)
    # file.close()
    # return latest_index

    @classmethod
    def build_index_from_last_24h(cls, signal_type, storage_path, bucket_width) -> None:
        """Create an index"""
        d = timedelta(days=1)

        past_day_content = TimeBucketizer.get_records(
            (datetime.now() - d),
            datetime.now(),
            signal_type,
            storage_path,
            bucket_width,
            HashRecord,
        )

        record_list = []
        for record in past_day_content:
            record_list.append((record.content_hash, record.content_id))
        testIndex = PDQIndex.build(record_list)
        return testIndex

    @classmethod
    def override_recent_index(
        cls, index: SignalTypeIndex, signal_type, storage_path, bucket_width, write_path
    ) -> None:
        """
        get most recent index of type PDQ
        write most recent index of specific index type
        """
        d = timedelta(days=1)
        pickle.dump(
            index, f"{write_path}''{signal_type}''{datetime.now()-bucket_width}"
        )
        # # variable name with creation time, index type, time delta value
        # indexObj = {testIndex, datetime.now(), PDQIndex, d}
        # # write_path = open(indexpath,"w")
        # pickle.dump(indexObj, write_path)
        # # example file structure
        # # "/var/data/threatexchange/LCCIndexes/<hash_type>/2022-02-08-20-45-<pickle-name>.pickle"
        # # os.listdirs, check if this returns sorted list of files
