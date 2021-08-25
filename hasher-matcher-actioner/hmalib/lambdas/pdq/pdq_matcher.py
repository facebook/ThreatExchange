# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import os
import pickle
import boto3
import datetime
import time
import typing as t
from mypy_boto3_sns import SNSClient

from threatexchange.signal_type.pdq_index import PDQIndex
from threatexchange.signal_type.pdq import PdqSignal

from hmalib import metrics
from hmalib.common.models.pipeline import MatchRecord
from hmalib.common.messages.match import BankedSignal, MatchMessage
from hmalib.common.models.signal import ThreatExchangeSignalMetadata
from hmalib.common.logging import get_logger
from hmalib.common.config import HMAConfig
from hmalib.common.configs.fetcher import ThreatExchangeConfig
from functools import lru_cache

from hmalib.indexers.s3_indexers import S3BackedPDQIndex

logger = get_logger(__name__)
s3_client = boto3.client("s3")
sns_client: SNSClient = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")

CACHED_TIME = 300
THRESHOLD = 31
LOCAL_INDEX_FILENAME = "/tmp/hashes.index"

INDEXES_BUCKET_NAME = os.environ["INDEXES_BUCKET_NAME"]
OUTPUT_TOPIC_ARN = os.environ["PDQ_MATCHES_TOPIC_ARN"]

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
HMA_CONFIG_TABLE = os.environ["HMA_CONFIG_TABLE"]
HMAConfig.initialize(HMA_CONFIG_TABLE)


@lru_cache(maxsize=None)
def get_index(bucket_name):
    """
    Load the given index from the s3 bucket and deserialize it
    """
    # TODO Cache this index for a period of time to reduce S3 calls and bandwidth.
    with metrics.timer(metrics.names.pdq_matcher_lambda.download_index):
        with open(LOCAL_INDEX_FILENAME, "wb") as index_file:
            s3_client.download_fileobj(
                bucket_name, S3BackedPDQIndex._get_index_s3_key(), index_file
            )

    with metrics.timer(metrics.names.pdq_matcher_lambda.parse_index):
        result = pickle.load(open(LOCAL_INDEX_FILENAME, "rb"))

    return result


@lru_cache(maxsize=128)
def get_privacy_group_matcher_active(privacy_group_id: str, _) -> bool:
    config = ThreatExchangeConfig.get(privacy_group_id)
    if not config:
        logger.warning("Privacy group %s is not found!", privacy_group_id)
        return False
    logger.info("matcher_active for %s is %s", privacy_group_id, config.matcher_active)
    return config.matcher_active


def lambda_handler(event, context):
    """
    TODO/FIXME migrate this lambda to be a part of matcher.py

    Listens to SQS events fired when new hash is generated. Loads the index
    stored in an S3 bucket and looks for a match.

    As per the default configuration
    - the index data bucket is INDEXES_BUCKET_NAME
    - the key name must be S3BackedPDQIndex._get_index_s3_key()

    When matched, publishes a notification to an SNS endpoint. Note this is in
    contrast with hasher and indexer. They publish to SQS directly. Publishing
    to SQS implies there can be only one consumer.

    Because, here, in the matcher, we publish to SNS, we can plug multiple
    queues behind it and profit!
    """
    records_table = dynamodb.Table(DYNAMODB_TABLE)

    hash_index: PDQIndex = get_index(INDEXES_BUCKET_NAME)
    logger.info("loaded_hash_index")

    for sqs_record in event["Records"]:
        message = json.loads(sqs_record["body"])
        if message.get("Event") == "TestEvent":
            logger.info("Disregarding Test Event")
            continue

        hash_str = message["hash"]
        key = message["key"]
        current_datetime = datetime.datetime.now()

        with metrics.timer(metrics.names.pdq_matcher_lambda.search_index):
            results = hash_index.query(hash_str)

        if results:
            match_ids = []
            matching_banked_signals: t.List[BankedSignal] = []
            for match in results:
                metadata = match.metadata
                logger.info(
                    "Match found for key: %s, hash %s -> %s", key, hash_str, metadata
                )
                privacy_group_list = metadata.get("privacy_groups", [])
                metadata["privacy_groups"] = list(
                    filter(
                        lambda x: get_privacy_group_matcher_active(
                            str(x),
                            time.time() // CACHED_TIME,
                            # CACHED_TIME default to 300 seconds, this will convert time.time() to an int parameter which changes every 300 seconds
                        ),
                        privacy_group_list,
                    )
                )
                if metadata["privacy_groups"]:
                    signal_id = str(metadata["id"])

                    with metrics.timer(
                        metrics.names.pdq_matcher_lambda.write_match_record
                    ):
                        # TODO: Add source (threatexchange) tags to match record
                        MatchRecord(
                            key,
                            PdqSignal,
                            hash_str,
                            current_datetime,
                            signal_id,
                            metadata["source"],
                            metadata["hash"],
                        ).write_to_table(records_table)

                    for pg in metadata.get("privacy_groups", []):
                        # Only update the metadata if it is not found in the table
                        # once intally created it is the fetcher's job to keep the item up to date
                        PDQSignalMetadata(
                            signal_id,
                            pg,
                            current_datetime,
                            metadata["source"],
                            metadata["hash"],
                            metadata["tags"].get(pg, []),
                        ).write_to_table_if_not_found(records_table)

                    match_ids.append(signal_id)

                    # TODO: change naming upstream and here from privacy_group[s]
                    # to dataset[s]
                    for privacy_group in metadata.get("privacy_groups", []):
                        banked_signal = BankedSignal(
                            str(signal_id), str(privacy_group), str(metadata["source"])
                        )
                        for tag in metadata["tags"].get(privacy_group, []):
                            banked_signal.add_classification(tag)
                        matching_banked_signals.append(banked_signal)

            # TODO: Add source (threatexchange) tags to match message
            if matching_banked_signals:
                match_message = MatchMessage(
                    content_key=key,
                    content_hash=hash_str,
                    matching_banked_signals=matching_banked_signals,
                )

                logger.info(f"Publishing match_message: {match_message}")

                # Publish one message for the set of matches.
                sns_client.publish(
                    TopicArn=OUTPUT_TOPIC_ARN, Message=match_message.to_aws_json()
                )

        else:
            logger.info(f"No matches found for key: {key} hash: {hash_str}")

    metrics.flush()
