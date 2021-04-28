# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import os
import pickle
import boto3
import datetime
import typing as t
from mypy_boto3_sns import SNSClient

from threatexchange.signal_type.pdq_index import PDQIndex

from hmalib import metrics
from hmalib.models import PDQMatchRecord
from hmalib.common.message_models import BankedSignal, MatchMessage
from hmalib.common.signal_models import PDQSignalMetadata
from hmalib.common.logging import get_logger

logger = get_logger(__name__)
s3_client = boto3.client("s3")
sns_client: SNSClient = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")

THRESHOLD = 31
LOCAL_INDEX_FILENAME = "/tmp/hashes.index"

INDEXES_BUCKET_NAME = os.environ["INDEXES_BUCKET_NAME"]
PDQ_INDEX_KEY = os.environ["PDQ_INDEX_KEY"]
OUTPUT_TOPIC_ARN = os.environ["PDQ_MATCHES_TOPIC_ARN"]

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]


def get_index(bucket_name, key):
    """
    Load the given index from the s3 bucket and deserialize it
    """
    # TODO Cache this index for a period of time to reduce S3 calls and bandwidth.
    with metrics.timer(metrics.names.pdq_matcher_lambda.download_index):
        with open(LOCAL_INDEX_FILENAME, "wb") as index_file:
            s3_client.download_fileobj(bucket_name, key, index_file)

    with metrics.timer(metrics.names.pdq_matcher_lambda.parse_index):
        result = pickle.load(open(LOCAL_INDEX_FILENAME, "rb"))

    return result


def lambda_handler(event, context):
    """
    Listens to SQS events fired when new hash is generated. Loads the index
    stored in an S3 bucket and looks for a match.

    As per the default configuration
    - the index data bucket is INDEXES_BUCKET_NAME
    - the key name must be PDQ_INDEX_KEY

    When matched, publishes a notification to an SNS endpoint. Note this is in
    contrast with hasher and indexer. They publish to SQS directly. Publishing
    to SQS implies there can be only one consumer.

    Because, here, in the matcher, we publish to SNS, we can plug multiple
    queues behind it and profit!
    """
    records_table = dynamodb.Table(DYNAMODB_TABLE)

    hash_index: PDQIndex = get_index(INDEXES_BUCKET_NAME, PDQ_INDEX_KEY)
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
                signal_id = metadata["id"]

                # TODO: Add source (threatexchange) tags to match record
                PDQMatchRecord(
                    key,
                    hash_str,
                    current_datetime,
                    signal_id,
                    metadata["source"],
                    metadata["hash"],
                ).write_to_table(records_table)

                for pg in metadata.get("privacy_groups", []):
                    # TODO: we might be able to get away with some 'if exists/upsert' here
                    # TODO: @BarrettOlson Write if don't exist or only update given fields is now needed!
                    PDQSignalMetadata(
                        signal_id,
                        pg,
                        current_datetime,
                        metadata["source"],
                        metadata["hash"],
                        metadata["tags"].get(pg, []),
                    ).write_to_table(records_table)

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
