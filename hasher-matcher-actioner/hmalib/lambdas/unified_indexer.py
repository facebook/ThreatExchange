# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import json
import typing as t
import functools
from collections import defaultdict

from urllib.parse import unquote_plus
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal

from threatexchange.signal_type.signal_base import SignalType

from hmalib.common.s3_adapters import (
    HashRowT,
    ThreatExchangeS3PDQAdapter,
    ThreatExchangeS3VideoMD5Adapter,
    ThreatUpdateS3Store,
    S3ThreatDataConfig,
)
from hmalib.common.logging import get_logger
from hmalib import metrics
from hmalib.common.mappings import INDEX_MAPPING
from hmalib.indexers.s3_indexers import (
    S3BackedInstrumentedIndexMixin,
)

logger = get_logger(__name__)

THREAT_EXCHANGE_DATA_BUCKET_NAME = os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"]
THREAT_EXCHANGE_DATA_FOLDER = os.environ["THREAT_EXCHANGE_DATA_FOLDER"]

INDEXES_BUCKET_NAME = os.environ["INDEXES_BUCKET_NAME"]


def merge_threat_exchange_files(
    accumulator: t.Dict[str, HashRowT], hash_row: HashRowT
) -> t.Dict[str, HashRowT]:
    hash, meta_data = hash_row
    if hash not in accumulator.keys():
        # Add hash as new row
        accumulator[hash] = hash_row
    else:
        # Add new privacy group to existing row
        accumulator[hash][1]["privacy_groups"].update(meta_data["privacy_groups"])
        # Add new 'tags' for privacy group to existing row
        accumulator[hash][1]["tags"].update(meta_data["tags"])
    return accumulator


# Maps from signal type to the subclass of ThreatExchangeS3Adapter.
# ThreatExchangeS3Adapter is used to fetch all the data corresponding to a
# signal_type. At some point, we must allow _updates_ to indexes rather than
# rebuilding them all the time.
_ADAPTER_MAPPING = {
    PdqSignal: ThreatExchangeS3PDQAdapter,
    VideoMD5Signal: ThreatExchangeS3VideoMD5Adapter,
}

# Which signal types must be processed into an index?
ALL_INDEXABLE_SIGNAL_TYPES = [PdqSignal, VideoMD5Signal]


def lambda_handler(event, context):
    """
    Runs on a schedule. On each run, gets all data files for
    ALL_INDEXABLE_SIGNAL_TYPES from s3, converts the raw data file into an index
    and writes to an output S3 bucket.

    As per the default configuration, the bucket must be
    - the hashing data bucket eg. dipanjanm-hashing-<...>
    - the key name must be in the ThreatExchange folder (eg.
      threat_exchange_data/)
    - the key name must return a signal_type in
      ThreatUpdateS3Store.get_signal_type_from_object_key
    """
    # Note: even though we know which files were updated, threatexchange indexes
    # do not yet allow adding new entries. So, we must do a full rebuild. So, we
    # only end up using the signal types that were updated, not the actual files
    # that changed.

    s3_config = S3ThreatDataConfig(
        threat_exchange_data_bucket_name=THREAT_EXCHANGE_DATA_BUCKET_NAME,
        threat_exchange_data_folder=THREAT_EXCHANGE_DATA_FOLDER,
    )

    for signal_type in ALL_INDEXABLE_SIGNAL_TYPES:
        adapter_class = _ADAPTER_MAPPING[signal_type]
        data_files = adapter_class(
            config=s3_config, metrics_logger=metrics.names.indexer
        ).load_data()

        with metrics.timer(metrics.names.indexer.merge_datafiles):
            logger.info(f"Merging {signal_type} Hash files")
            flattened_data = [
                hash_row for file_ in data_files.values() for hash_row in file_
            ]

            merged_data = functools.reduce(
                merge_threat_exchange_files, flattened_data, {}
            ).values()

        with metrics.timer(metrics.names.indexer.build_index):
            logger.info(f"Rebuilding {signal_type} Index")

            for index_class in INDEX_MAPPING[signal_type]:
                index: S3BackedInstrumentedIndexMixin = index_class.build(merged_data)

                logger.info(
                    f"Putting {signal_type} index in S3 for index {index.get_index_class_name()}"
                )
                index.save(bucket_name=INDEXES_BUCKET_NAME)
            metrics.flush()

    logger.info("Index updates complete")
