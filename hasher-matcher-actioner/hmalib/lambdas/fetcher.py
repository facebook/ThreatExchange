# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of the "fetcher" module of HMA.

Fetching involves connecting to the ThreatExchange API and downloading
signals to synchronize a local copy of the database, which will then
be fed into various indices.
"""

import collections
import csv
import io
import json
import logging
import os
import sys
import tempfile
import typing as t
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.errorfactory import ClientError
from hmalib.aws_secrets import AWSSecrets
from hmalib.common import get_logger
from threatexchange import threat_updates as tu
from threatexchange.api import ThreatExchangeAPI
from threatexchange.cli.dataset.simple_serialization import CliIndicatorSerialization
from threatexchange.descriptor import SimpleDescriptorRollup
from threatexchange.signal_type.pdq import PdqSignal


logger = get_logger(__name__)

dynamodb = boto3.resource("dynamodb")
s3 = boto3.resource("s3")


@dataclass
class FetcherConfig:
    """
    Simple holder for getting typed environment variables
    """

    s3_bucket: str
    s3_te_data_folder: str
    collab_config_table: str

    @classmethod
    @lru_cache(maxsize=1)  # probably overkill, but at least it's consistent
    def get(cls):
        return cls(
            s3_bucket=os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"],
            s3_te_data_folder=os.environ["THREAT_EXCHANGE_DATA_FOLDER"],
            collab_config_table=os.environ["THREAT_EXCHANGE_CONFIG_DYNAMODB"],
        )


def lambda_handler(event, context):
    config = FetcherConfig.get()

    paginator = dynamodb.meta.client.get_paginator("scan")

    response_iterator = paginator.paginate(
        TableName=config.collab_config_table,
        ProjectionExpression=",".join(("#Name", "privacy_group", "tags")),
        ExpressionAttributeNames={"#Name": "Name"},
    )

    collabs = []
    for page in response_iterator:
        for item in page["Items"]:
            collabs.append((item["Name"], item["privacy_group"]))

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    names = [collab[0] for collab in collabs[:5]]
    if len(names) < len(collabs):
        names[-1] = "..."

    data = f"Triggered at time {current_time}, found {len(collabs)} collabs: {', '.join(names)}"
    logger.info(data)

    api_key = AWSSecrets.te_api_key()
    api = ThreatExchangeAPI(api_key)

    te_data_bucket = s3.Bucket(config.s3_bucket)

    stores = []
    for name, privacy_group in collabs:
        logger.info("Processing updates for collaboration %s", name)

        indicator_store = ThreatUpdateS3PDQStore(
            privacy_group,
            api.app_id,
            te_data_bucket,
            config.s3_te_data_folder,
        )
        stores.append(indicator_store)
        indicator_store.load_checkpoint()
        if indicator_store.stale:
            logger.warning("Store for %s - %d stale! Resetting.", name, privacy_group)
            indicator_store.reset()

        if indicator_store.fetch_checkpoint >= now.timestamp():
            continue

        delta = indicator_store.next_delta

        try:
            delta.incremental_sync_from_threatexchange(
                api,
            )
        except:
            # Don't need to call .exception() here because we're just re-raising
            logger.error("Exception occurred! Attempting to save...")
            # Force delta to show finished
            delta.end = delta.current
            raise
        finally:
            if delta:
                logging.info("Fetch complete, applying %d updates", len(delta.updates))
                indicator_store.apply_updates(delta)
            else:
                logging.error("Failed before fetching any records")

    # TODO add TE data to indexer

    return {"statusCode": 200, "body": "Sure Yeah why not"}


class ThreatUpdateS3PDQStore(tu.ThreatUpdatesStore):
    """
    Store files in S3!
    """

    def __init__(
        self,
        privacy_group: int,
        app_id: int,
        s3_bucket: t.Any,  # Not typable?
        s3_te_data_folder: str,
    ) -> None:
        super().__init__(privacy_group)
        self.app_id = app_id
        self._cached_state: t.Optional[t.Dict] = None
        self.s3_bucket = s3_bucket
        self.s3_te_data_folder = s3_te_data_folder

    @property
    def checkpoint_s3_key(self) -> str:
        return f"{self.s3_te_data_folder}{self.privacy_group}.checkpoint"

    @property
    def data_s3_key(self) -> str:
        return f"{self.s3_te_data_folder}{self.privacy_group}.pdq.te"

    @property
    def next_delta(self) -> tu.ThreatUpdatesDelta:
        """
        Hacky - we only support PDQ right now, force to only fetch that
        Eventually want to always download everything and choose what to
        do with it later, though checkpoints will need to be reset

        IF YOU CHANGE THIS, OLD CHECKPOINTS NEED TO BE INVALIDATED TO
        GET THE NON-PDQ DATA!
        """
        delta = super().next_delta
        delta.types = ["HASH_PDQ"]
        return delta

    def reset(self):
        super().reset()
        self._cached_state = None

    def _load_checkpoint(self) -> tu.ThreatUpdateCheckpoint:
        """Load the state of the threat_updates checkpoints from state directory"""
        txt_content = read_s3_text(self.s3_bucket, self.checkpoint_s3_key)
        if txt_content is None:
            logger.warning("No s3 checkpoint for %d. First run?", self.privacy_group)
            return tu.ThreatUpdateCheckpoint()
        checkpoint_json = json.load(txt_content)

        ret = tu.ThreatUpdateCheckpoint(
            checkpoint_json["last_fetch_time"],
            checkpoint_json["fetch_checkpoint"],
        )
        logger.info(
            "Loaded checkpoint for %d. last_fetch_time=%d fetch_checkpoint=%d",
            self.privacy_group,
            ret.last_fetch_time,
            ret.fetch_checkpoint,
        )

        return ret

    def _store_checkpoint(self, checkpoint: tu.ThreatUpdateCheckpoint) -> None:
        txt_content = io.StringIO()
        json.dump(
            {
                "last_fetch_time": checkpoint.last_fetch_time,
                "fetch_checkpoint": checkpoint.fetch_checkpoint,
            },
            txt_content,
            indent=2,
        )
        write_s3_text(txt_content, self.s3_bucket, self.checkpoint_s3_key)
        logger.info(
            "Stored checkpoint for %d. last_fetch_time=%d fetch_checkpoint=%d",
            self.privacy_group,
            checkpoint.last_fetch_time,
            checkpoint.fetch_checkpoint,
        )

    def load_state(self, allow_cached=True):
        if not allow_cached or self._cached_state is None:
            txt_content = read_s3_text(self.s3_bucket, self.data_s3_key)
            items = []
            if txt_content is None:
                logger.warning("No TE state for %d. First run?", self.privacy_group)
            else:
                # Violate your warranty with module state!
                csv.field_size_limit(65535)  # dodge field size problems
                for row in csv.reader(txt_content):
                    items.append(
                        CliIndicatorSerialization(
                            "HASH_PDQ",
                            row[0],
                            SimpleDescriptorRollup.from_row(row[1:]),
                        )
                    )
                logger.info("%d rows loaded for %d", len(items), self.privacy_group)
            # Do all in one assignment just in case of threads
            self._cached_state = {item.key: item for item in items}
        return self._cached_state

    def _store_state(self, contents: t.Iterable["CliIndicatorSerialization"]):
        row_by_type: t.DefaultDict = collections.defaultdict(list)
        for item in contents:
            row_by_type[item.indicator_type].append(item)
        # Discard all updates except PDQ
        items = row_by_type.get("HASH_PDQ", [])
        with io.StringIO(newline="") as txt_content:
            writer = csv.writer(txt_content)
            writer.writerows(item.as_csv_row() for item in items)
            write_s3_text(txt_content, self.s3_bucket, self.data_s3_key)
            logger.info("%d rows stored for %d", len(items), self.privacy_group)

    def _apply_updates_impl(self, delta: tu.ThreatUpdatesDelta) -> None:
        state: t.Dict = {}
        if delta.start > 0:
            state = self.load_state()
        for update in delta:
            item = CliIndicatorSerialization.from_threat_updates_json(
                self.app_id, update.raw_json
            )
            if update.should_delete:
                state.pop(item.key, None)
            else:
                state[item.key] = item

        self._store_state(state.values())
        self._cached_state = state


def read_s3_text(bucket, key: str) -> t.Optional[io.StringIO]:
    byte_content = io.BytesIO()
    try:
        bucket.download_fileobj(key, byte_content)
    except ClientError as ce:
        if ce.response["Error"]["Code"] != "404":
            raise
        return None
    return io.StringIO(byte_content.getvalue().decode())


def write_s3_text(txt_content: io.StringIO, bucket, key: str) -> None:
    byte_content = io.BytesIO(txt_content.getvalue().encode())
    bucket.upload_fileobj(byte_content, key)


# for silly testing purposes
# run from hasher-matcher-actioner with
# python3 -m hmalib.lambdas.fetcher

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    FetcherConfig.get.cache_clear()  # Just in case
    FetcherConfig.get()

    # This will only kinda work for so long - eventually will
    # need to use a proper harness
    lambda_handler(None, None)
