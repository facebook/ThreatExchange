# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of the "fetcher" module of HMA.

Fetching involves connecting to the ThreatExchange API and downloading
signals to synchronize a local copy of the database, which will then
be fed into various indices.
"""

import boto3
from botocore.errorfactory import ClientError
import os
import tempfile
import io
import csv

from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from functools import lru_cache

from threatexchange import threat_updates as tu
from threatexchange.cli.dataset.simple_serialization import CliIndicatorSerialization
from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.api import ThreatExchangeAPI

from hmalib.aws_secrets import AWSSecrets
from hmalib.common import get_logger


logger = get_logger(__name__)

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")



@dataclass
class FetcherConfig:
    """
    Simple holder for getting typed environment variables
    """

    output_s3_bucket: str
    output_s3_key: str
    collab_config_table: str

    @classmethod
    @lru_cache(maxsize=1)  # probably overkill, but at least it's consistent
    def get(cls):
        return cls(
            output_s3_bucket=os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"],
            output_s3_key = os.environ["THREAT_EXCHANGE_PDQ_DATA_KEY"],
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
        for item in page['Items']:
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

    stores = []
    for name, privacy_group in collabs:
        logger.info(f"Processing updates for collaboration {name}")
        # create temp dataset directory if doesnt exist
        collab_dataset_dir = tempfile.TemporaryDirectory(suffix=str(privacy_group))

        indicator_store = ThreatUpdateS3Store(
            Path(collab_dataset_dir.name),
            privacy_group,
            api.app_id,
            serialization=S3IndicatorSerialization,
        )
        stores.append(indicator_store)
        indicator_store.load_checkpoint()
        if indicator_store.stale:
            indicator_store.reset()

        if indicator_store.fetch_checkpoint >= now.timestamp():
            continue

        delta = indicator_store.next_delta
        # Hacky - we only support PDQ right now, force to only fetch that
        # Eventually want to always download everything and choose what to
        # do with it later, though checkpoints will need to be reset
        delta.types = ["HASH_PDQ"]

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
                indicator_store.apply_updates(delta)

    # TODO add TE data to indexer

    return {"statusCode": 200, "body": "Sure Yeah why not"}


class ThreatUpdateS3PDQStore(ThreatUpdatesStore):
    """
    Store files in S3!
    """

    CHECKPOINT_S3_KEY_SUFFIX = "checkpoint"
    DATA_S3_KEY_SUFFIX = "te"

    def __init__(
        self,
        privacy_group: int,
        app_id: int,
        s3_bucket: boto3.Bucket
        *,
        types: t.Iterable[str] = (),
    ) -> None:
        super().__init__(privacy_group, types)
        self.app_id = app_id
        self._cached_state = None
        self._s3_bucket = s3_bucket

    @property
    def checkpoint_s3_key(self) -> str:
        return f"{self._s3_key}.{self.CHECKPOINT_S3_KEY_SUFFIX}"

    @property
    def data_s3_key(self) -> str:
        return f"{self.privacy_group}.{self.DATA_S3_KEY_SUFFIX}"

    def _load_checkpoint(self) -> ThreatUpdateCheckpoint:
        """Load the state of the threat_updates checkpoints from state directory"""

        content = io.StringIO()
        try:
            self.s3_bucket.download_fileobj(self.checkpoint_s3_key, content)
        except ClientError as ce:
            if ce.response['Error']['Code'] == "404":
                return ThreatUpdateCheckpoint()
            raise

        content.seek(0)
        checkpoint_json = json.load(content)

        return ThreatUpdateCheckpoint(
            checkpoint_json["last_fetch_time"],
            checkpoint_json["fetch_checkpoint"],
        )

    def _store_checkpoint(self, checkpoint: ThreatUpdateCheckpoint) -> None:
        serialized_checkpoint = json.dumps(
            {
                "last_fetch_time": checkpoint.last_fetch_time,
                "fetch_checkpoint": checkpoint.fetch_checkpoint,
            },
            indent=2,
        )
        self.bucket.put_object(
            Bucket=INDEXES_BUCKET_NAME, Key=PDQ_INDEX_KEY, Body=serialized_checkpoint
        )

    def load_state(self, allow_cached=True):
        if not allow_cached or self._cached_state is None:
            content = io.StringIO(newline="")
            try:
                self.s3_bucket.download_fileobj(self.data_s3_key, content)
            except ClientError as ce:
                if ce.response['Error']['Code'] != "404":
                    raise
            content.seek(0)
            # Violate your warranty with module state!
            items = []
            csv.field_size_limit(sys.maxsize)  # dodge field size problems
            for row in csv.reader(content):
                items.append(
                    CliIndicatorSerialization(
                        "HASH_PDQ",
                        row[0],
                        SimpleDescriptorRollup.from_row(row[1:]),
                    )
                )
            # Do all in one assignment just in case of threads
            self._cached_state = {
                item.key: item for item in items
            }
        return self._cached_state

    def _store_state(
        self, contents: t.Iterable["CliIndicatorSerialization"]
    ):
        row_by_type = collections.defaultdict(list)
        for item in contents:
            row_by_type[item.indicator_type].append(item)
        ret = []
        for items in row_by_type.get("HASH_PDQ", []):
            with io.StringIO(newline="") as content:
                writer = csv.writer(content)
                writer.writerows(item.as_csv_row() for item in items)
                self.s3_bucket.upload_fileobj(self.data_s3_key, content)
        return ret

    def _apply_updates_impl(self, delta: ThreatUpdatesDelta) -> None:
        os.makedirs(self.path, exist_ok=True)
        state = {}
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

        self._cached_state = state
        CliIndicatorSerialization.store(self.path, state.values())


# for silly testing purposes
# run from hasher-matcher-actioner with
# python3 -m hmalib.lambdas.fetcher
if __name__ == "__main__":
    config = FetcherConfig.get()
    config.output_s3_bucket = "my-fake-bucket",
    config.collab_config_table = "jeberl-ThreatExchangeConfig",

    lambda_handler(None, None)
