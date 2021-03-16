# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import boto3
import json
from datetime import datetime
import os
from dataclasses import dataclass
from functools import lru_cache

dynamodb = boto3.resource("dynamodb")


@dataclass
class FetcherConfig:

    output_s3_bucket: str
    collab_config_table: str

    @classmethod
    @lru_cache(maxsize=1)  # probably overkill, but at least it's consistent
    def get(cls):
        return cls(
            output_s3_bucket=os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"],
            collab_config_table=os.environ["THREAT_EXCHANGE_CONFIG_DYNAMODB"],
        )


def lambda_handler(event, context):
    config = FetcherConfig.get()

    paginator = dynamodb.meta.client.get_paginator("scan")

    response_iterator = paginator.paginate(
        TableName=config.collab_config_table,
        ProjectionExpression=",".join(("#name", "privacy_group", "tags")),
        ExpressionAttributeNames={"#name": "name"},
    )

    collabs = []
    for page in response_iterator:
        for item in page["Items"]:
            name = item["name"]
            privacy_group = item["privacy_group"]
            collabs.append((name, privacy_group))

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    names = [v[0] for v in collabs[:5]]
    if len(names) > len(collabs):
        names[-1] = "..."

    data = f"Triggered at time {current_time}, found {len(collabs)} collabs: {', '.join(names)}"
    print(data)

    # TODO fetch data from ThreatExchange
    threat_exchange_data = [{"should_delete": False, "data": data}]

    # TODO add TE data to indexer

    return {"statusCode": 200, "body": json.dumps(threat_exchange_data)}
