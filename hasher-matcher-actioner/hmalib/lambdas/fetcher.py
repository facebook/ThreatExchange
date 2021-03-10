# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import boto3
import os
import shutil
import pathlib

from datetime import datetime
from dataclasses import dataclass
from functools import lru_cache

from threatexchange.threat_updates import ThreatUpdateFileStore
from threatexchange.signal_type.pdq_index import PDQIndex

from threatexchange.cli.dataset.simple_serialization import CliIndicatorSerialization
from threatexchange.api import ThreatExchangeAPI

## Add hmalib to python path
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
parentdir = os.path.dirname(parentdir)
sys.path.append(parentdir)

from hmalib.aws_secrets import AWSSecrets

# THREAT_EXCHANGE_DATA_BUCKET_NAME = os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"]

indecies = [PDQIndex]

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")

dataset_folder = pathlib.Path("temp_te_data")

@dataclass
class FetcherConfig:

    output_s3_bucket: str
    collab_config_table: str

    @classmethod
    @lru_cache(maxsize=1)  # probably overkill, but at least it's consistent
    def get(cls):
        return cls(
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
            collabs.append((item["Name"], item["privacy_group"][0]))

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    names = [collab[0] for collab in collabs[:5]]
    if len(names) < len(collabs):
        names[-1] = "..."

    data = f"Triggered at time {current_time}, found {len(collabs)} collabs: {', '.join(names)}"
    print(data)

    api_key = AWSSecrets.te_api_key()
    api = ThreatExchangeAPI(api_key)

    stores = []
    for name, privacy_group in collabs:
        print(f"Processing updates for collaboration {name}")
        # create empty temp dataset folder if doesnt exist
        collab_dataset_folder = dataset_folder / privacy_group
        if os.path.exists(collab_dataset_folder) and os.path.isdir(collab_dataset_folder):
            shutil.rmtree(collab_dataset_folder)
        os.mkdir(collab_dataset_folder)

        indicator_store = ThreatUpdateFileStore(
            collab_dataset_folder,
            privacy_group,
            api.app_id,
            serialization=CliIndicatorSerialization,
            types=[index_cls.data_type() for index_cls in indecies]
        )
        stores.append(indicator_store)
        indicator_store.load_checkpoint()
        if indicator_store.stale:
            indicator_store.reset()

        if indicator_store.fetch_checkpoint >= now.timestamp():
            continue

        delta = indicator_store.next_delta
        try:
            delta.incremental_sync_from_threatexchange(
                api,
                # progress_fn=print
            )
        except:
            print("Exception occurred! Attempting to save...")
            # Force delta to show finished
            delta.end = delta.current
            raise
        finally:
            if delta:
                indicator_store.apply_updates(delta)

    # TODO add TE data to indexer

    return {"statusCode": 200, "body": "Sure Yeah why not"}

lambda_handler(None, None)
