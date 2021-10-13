# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of the "fetcher" module of HMA.

Fetching involves connecting to the ThreatExchange API and downloading
signals to synchronize a local copy of the database, which will then
be fed into various indices.
"""

import logging
import time
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import DefaultDict
import boto3

from threatexchange.api import ThreatExchangeAPI
from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.threat_updates import ThreatUpdateJSON

from hmalib.aws_secrets import AWSSecrets
from hmalib.common.config import HMAConfig
from hmalib.common.logging import get_logger
from hmalib.common.configs.fetcher import ThreatExchangeConfig
from hmalib.common.s3_adapters import ThreatUpdateS3Store


logger = get_logger(__name__)
dynamodb = boto3.resource("dynamodb")

# In one fetcher run, how many descriptor updates to fetch per privacy group
# using /threat_updates
MAX_DESCRIPTORS_UPDATED = 20000

# Print progress when polling threat_updates once every...<> seconds
PROGRESS_PRINT_INTERVAL_SEC = 20


@lru_cache(maxsize=None)
def get_s3_client():
    return boto3.client("s3")


# Lambda init tricks
@lru_cache(maxsize=1)
def lambda_init_once():
    """
    Do some late initialization for required lambda components.

    Lambda initialization is weird - despite the existence of perfectly
    good constructions like __name__ == __main__, there don't appear
    to be easy ways to split your lambda-specific logic from your
    module logic except by splitting up the files and making your
    lambda entry as small as possible.

    TODO: Just refactor this file to separate the lambda and functional
          components
    """
    cfg = FetcherConfig.get()
    HMAConfig.initialize(cfg.config_table_name)


@dataclass
class FetcherConfig:
    """
    Simple holder for getting typed environment variables
    """

    s3_bucket: str
    s3_te_data_folder: str
    config_table_name: str
    data_store_table: str

    @classmethod
    @lru_cache(maxsize=None)  # probably overkill, but at least it's consistent
    def get(cls):
        # These defaults are naive but can be updated for testing purposes.
        return cls(
            s3_bucket=os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"],
            s3_te_data_folder=os.environ["THREAT_EXCHANGE_DATA_FOLDER"],
            config_table_name=os.environ["CONFIG_TABLE_NAME"],
            data_store_table=os.environ["DYNAMODB_DATASTORE_TABLE"],
        )


def is_int(int_string: str):
    """
    Checks if string is convertible to int.
    """
    try:
        int(int_string)
        return True
    except ValueError:
        return False


class ProgressLogger:
    """
    Use this to get a progress logger which counts up the number of items
    processed via /threat_updates.

    Returns a callable class.
    """

    def __init__(self):
        self.processed = 0
        self.last_update_time = None
        self.counts = defaultdict(lambda: 0)
        self.last_update_printed = 0

    def __call__(self, update: ThreatUpdateJSON):
        self.processed += 1
        self.counts[update.threat_type] += -1 if update.should_delete else 1
        self.last_update_time = update.time

        now = time.time()
        if now - self.last_update_printed >= PROGRESS_PRINT_INTERVAL_SEC:
            self.last_update_printed = now
            logger.info("threat_updates/: processed %d descriptors.", self.processed)


def lambda_handler(_event, _context):
    """
    Run through threatexchange privacy groups and fetch updates to them. If this
    is the first time for a privacy group, will fetch from the start, else only
    updates since the last time.

    Note: since this is a scheduled job, we swallow all exceptions. We only log
    exceptions and move on.
    """

    lambda_init_once()
    config = FetcherConfig.get()
    collabs = ThreatExchangeConfig.get_all()

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    names = [collab.privacy_group_name for collab in collabs[:5]]
    if len(names) < len(collabs):
        names[-1] = "..."

    data = f"Triggered at time {current_time}, found {len(collabs)} collabs: {', '.join(names)}"
    logger.info(data)

    api_key = AWSSecrets().te_api_key()
    api = ThreatExchangeAPI(api_key)

    for collab in collabs:
        logger.info(
            "Processing updates for collaboration %s", collab.privacy_group_name
        )

        if not is_int(collab.privacy_group_id):
            logger.info(
                f"Fetch skipped because privacy_group_id({collab.privacy_group_id}) is not an int"
            )
            continue

        indicator_store = ThreatUpdateS3Store(
            int(collab.privacy_group_id),
            api.app_id,
            s3_client=get_s3_client(),
            s3_bucket_name=config.s3_bucket,
            s3_te_data_folder=config.s3_te_data_folder,
            data_store_table=config.data_store_table,
            supported_signal_types=[VideoMD5Signal, PdqSignal],
        )

        try:
            indicator_store.load_checkpoint()

            if indicator_store.stale:
                logger.warning(
                    "Store for %s - %d stale! Resetting.",
                    collab.privacy_group_name,
                    int(collab.privacy_group_id),
                )
                indicator_store.reset()

            if indicator_store.fetch_checkpoint >= now.timestamp():
                continue

            delta = indicator_store.next_delta

            delta.incremental_sync_from_threatexchange(
                api, limit=MAX_DESCRIPTORS_UPDATED, progress_fn=ProgressLogger()
            )
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "Encountered exception while getting updates. Will attempt saving.."
            )
            # Force delta to show finished
            delta.end = delta.current
        finally:
            if delta:
                logging.info("Fetch complete, applying %d updates", len(delta.updates))
                indicator_store.apply_updates(
                    delta, post_apply_fn=indicator_store.post_apply
                )
            else:
                logging.error("Failed before fetching any records")
