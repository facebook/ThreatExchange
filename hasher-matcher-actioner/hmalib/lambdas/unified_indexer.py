# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import typing as t
import functools
import boto3

from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.signal_type.signal_base import SignalType

from hmalib.common.models.bank import BanksTable
from hmalib.common.s3_adapters import (
    HashRowT,
    ThreatExchangeS3Adapter,
    ThreatExchangeS3PDQAdapter,
    ThreatExchangeS3VideoMD5Adapter,
    S3ThreatDataConfig,
)
from hmalib.common.logging import get_logger
from hmalib import metrics
from hmalib.common.mappings import INDEX_MAPPING
from hmalib.indexers.metadata import BankedSignalIndexMetadata
from hmalib.indexers.s3_indexers import (
    S3BackedInstrumentedIndexMixin,
)

logger = get_logger(__name__)
dynamodb = boto3.resource("dynamodb")

THREAT_EXCHANGE_DATA_BUCKET_NAME = os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"]
THREAT_EXCHANGE_DATA_FOLDER = os.environ["THREAT_EXCHANGE_DATA_FOLDER"]

INDEXES_BUCKET_NAME = os.environ["INDEXES_BUCKET_NAME"]
BANKS_TABLE = os.environ["BANKS_TABLE"]


def get_all_bank_hash_rows(
    signal_type: t.Type[SignalType], banks_table: BanksTable
) -> t.Iterable[HashRowT]:
    """
    Make repeated calls to banks table to get all hashes for a signal type.

    Returns list[HashRowT]. HashRowT is a tuple of hash_value and some metadata
    about the signal.
    """

    exclusive_start_key = None
    hash_rows: t.List[HashRowT] = []

    while True:
        page = banks_table.get_bank_member_signals_to_process_page(
            signal_type=signal_type, exclusive_start_key=exclusive_start_key
        )

        for bank_member_signal in page.items:
            hash_rows.append(
                (
                    bank_member_signal.signal_value,
                    [
                        BankedSignalIndexMetadata(
                            bank_member_signal.signal_id,
                            bank_member_signal.signal_value,
                            bank_member_signal.bank_member_id,
                        ),
                    ],
                )
            )

        exclusive_start_key = page.last_evaluated_key
        if not page.has_next_page():
            break

    logger.info(
        f"Obtained {len(hash_rows)} hash records from banks for signal_type:{signal_type.get_name()}"
    )

    return hash_rows


def merge_hash_rows_on_hash_value(
    accumulator: t.Dict[str, HashRowT], hash_row: HashRowT
) -> t.Dict[str, HashRowT]:
    hash, metadata = hash_row
    if hash not in accumulator.keys():
        # Add hash as new row
        accumulator[hash] = hash_row
    else:
        # Append current metadata to existing row's metadata objects by
        # replacing completely. Tuples can't be updated, so replace.
        accumulator[hash] = (hash, list(metadata) + list(accumulator[hash][1]))

    return accumulator


# Maps from signal type to the subclass of ThreatExchangeS3Adapter.
# ThreatExchangeS3Adapter is used to fetch all the data corresponding to a
# signal_type. At some point, we must allow _updates_ to indexes rather than
# rebuilding them all the time.
_ADAPTER_MAPPING: t.Dict[t.Type[SignalType], t.Type[ThreatExchangeS3Adapter]] = {
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

    banks_table = BanksTable(dynamodb.Table(BANKS_TABLE))

    for signal_type in ALL_INDEXABLE_SIGNAL_TYPES:
        adapter_class = _ADAPTER_MAPPING[signal_type]
        data_files = adapter_class(
            config=s3_config, metrics_logger=metrics.names.indexer
        ).load_data()

        bank_data = get_all_bank_hash_rows(signal_type, banks_table)

        with metrics.timer(metrics.names.indexer.merge_datafiles):
            logger.info(f"Merging {signal_type} Hash files")

            # go from dict[filename, list<hash rows>] → list<hash rows>
            flattened_data = [
                hash_row for file_ in data_files.values() for hash_row in file_
            ]

            merged_data = functools.reduce(
                merge_hash_rows_on_hash_value, flattened_data + bank_data, {}
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
