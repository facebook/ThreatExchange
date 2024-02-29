# Copyright (c) Meta Platforms, Inc. and affiliates.

import glob
import os.path
import pathlib
import pickle
import time
import typing as t
from dataclasses import dataclass
from datetime import datetime, timedelta

from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.signal_type.pdq.pdq_index import PDQIndex
from hmalib import metrics

from hmalib.common.logging import get_logger
from hmalib.common.models.pipeline import HashRecord
from hmalib.common.timebucketizer import TimeBucketizer

starttime = time.time()
logger = get_logger(__name__)


class LCCIndexer:
    @classmethod
    def get_recent_index(cls, storage_path, signal_type) -> PDQIndex:
        """Get the most recent index."""
        directory = os.path.join(storage_path, signal_type)
        latest_directory = max(pathlib.Path(
            directory).glob("*/"), key=os.path.getmtime)

        with open(latest_directory, "rb") as f:
            return pickle.load(f)

    @classmethod
    def build_index_from_last_24h(cls, signal_type, storage_path, bucket_width) -> PDQIndex:
        """Create an index"""
        with metrics.timer(metrics.names.lcc.get_data):
            d = timedelta(days=1)

            # Make 3 different metric.timers
            # get_records, record_list, and .build
            past_day_content = TimeBucketizer.get_records(
                (datetime.now() - d),
                datetime.now(),
                signal_type,
                storage_path,
                bucket_width,
                HashRecord,
            )

        with metrics.timer(metrics.names.lcc.in_memory_processing):
            record_list = []
            for record in past_day_content:
                record_list.append((record.content_hash, record.content_id))

        with metrics.timer(metrics.names.lcc.build_index):
            return PDQIndex.build(record_list)

    @classmethod
    def override_recent_index(
        cls,
        index: SignalTypeIndex,
        signal_type,
        storage_path,
        bucket_width,
    ) -> None:
        """
        get most recent index of type PDQ
        write most recent index of specific index type
        """
        creation_time = str(datetime.now().strftime("%Y-%m-%d_%H:%M"))
        directory = os.path.join(storage_path, signal_type, creation_time)
        with open(directory, "wb") as f:
            pickle.dump(index, f)
