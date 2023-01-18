# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import typing as t
import functools
import boto3

from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.index import SignalTypeIndex

from hmalib.common.config import HMAConfig
from hmalib.common.models.bank import BanksTable
from hmalib.common.s3_adapters import (
    HashRowT,
    S3ThreatDataConfig,
)
from hmalib.common.logging import get_logger
from hmalib import metrics
from hmalib.indexers.metadata import BankedSignalIndexMetadata
from hmalib.indexers.index_store import S3PickledIndexStore
from hmalib.lambdas.common import get_signal_type_mapping

logger = get_logger(__name__)
dynamodb = boto3.resource("dynamodb")

THREAT_EXCHANGE_DATA_BUCKET_NAME = os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"]
THREAT_EXCHANGE_DATA_FOLDER = os.environ["THREAT_EXCHANGE_DATA_FOLDER"]

INDEXES_BUCKET_NAME = os.environ["INDEXES_BUCKET_NAME"]
BANKS_TABLE = os.environ["BANKS_TABLE"]
HMA_CONFIG_TABLE = os.environ["HMA_CONFIG_TABLE"]


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

    HMAConfig.initialize(HMA_CONFIG_TABLE)
    signal_content_mapping = get_signal_type_mapping()

    index_store = S3PickledIndexStore(INDEXES_BUCKET_NAME)
    banks_table = BanksTable(dynamodb.Table(BANKS_TABLE), signal_content_mapping)

    for signal_type in ALL_INDEXABLE_SIGNAL_TYPES:
        with metrics.timer(metrics.names.indexer.get_bank_data):
            bank_data = get_all_bank_hash_rows(signal_type, banks_table)

        with metrics.timer(metrics.names.indexer.merge_datafiles):
            logger.info(f"Merging {signal_type} Hash files")

            merged_data = functools.reduce(
                merge_hash_rows_on_hash_value, bank_data, {}
            ).values()

        with metrics.timer(metrics.names.indexer.build_index):
            logger.info(f"Rebuilding {signal_type} Index")

            index: SignalTypeIndex = signal_type.get_index_cls().build(merged_data)
            logger.info(f"Putting {signal_type} index in S3.")
            index_store.save(index)
            metrics.flush()

    logger.info("Index updates complete")
