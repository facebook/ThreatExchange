# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import boto3
import os
import tempfile

from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from functools import lru_cache

from threatexchange.threat_updates import ThreatUpdateFileStore
from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.cli.dataset.simple_serialization import CliIndicatorSerialization
from threatexchange.api import ThreatExchangeAPI

from hmalib.aws_secrets import AWSSecrets
from hmalib.common import get_logger

logger = get_logger(__name__)

signal_types = [PdqSignal]

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")

dataset_dir = tempfile.TemporaryDirectory()

@dataclass
class FetcherConfig:

    output_s3_bucket: str
    collab_config_table: str

    @classmethod
    @lru_cache(maxsize=1)  # probably overkill, but at least it's consistent
    def get(cls):
        return cls(
            # TODO read from environment variables
            # output_s3_bucket=os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"],
            # collab_config_table=os.environ["THREAT_EXCHANGE_CONFIG_DYNAMODB"],
            output_s3_bucket="my-fake-bucket",
            collab_config_table="jeberl-ThreatExchangeConfig",
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

        indicator_store = ThreatUpdateFileStore(
            Path(collab_dataset_dir.name),
            privacy_group,
            api.app_id,
            serialization=CliIndicatorSerialization,
        )
        stores.append(indicator_store)
        indicator_store.load_checkpoint()
        if indicator_store.stale:
            indicator_store.reset()

        if indicator_store.fetch_checkpoint >= now.timestamp():
            continue

        delta = indicator_store.next_delta
        # Hacky - we only support PDQ right now, force to only fetch that
        delta.types = [signal_type.INDICATOR_TYPE for signal_type in signal_types]

        try:
            delta.incremental_sync_from_threatexchange(
                api,
            )
        except:
            logger.info("Exception occurred! Attempting to save...")
            # Force delta to show finished
            delta.end = delta.current
            raise
        finally:
            if delta:
                indicator_store.apply_updates(delta)

    # TODO add TE data to indexer

    return {"statusCode": 200, "body": "Sure Yeah why not"}

if __name__ == "__main__":
    lambda_handler(None, None)
