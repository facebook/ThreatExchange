# Copyright (c) Meta Platforms, Inc. and affiliates.

import functools
import json
import os
import boto3
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from mypy_boto3_sns import SNSClient

from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal

from hmalib import metrics
from hmalib.common.logging import get_logger
from hmalib.common.models.bank import BanksTable
from hmalib.matchers.matchers_base import Matcher
from hmalib.common.config import HMAConfig
from hmalib.common.models.pipeline import PipelineHashRecord
from hmalib.lambdas.common import get_signal_type_mapping


INDEXES_BUCKET_NAME = os.environ["INDEXES_BUCKET_NAME"]
BANKS_TABLE = os.environ["BANKS_TABLE"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
HMA_CONFIG_TABLE = os.environ["HMA_CONFIG_TABLE"]
MATCHES_TOPIC_ARN = os.environ["MATCHES_TOPIC_ARN"]

HMAConfig.initialize(HMA_CONFIG_TABLE)


@functools.lru_cache(maxsize=None)
def get_dynamodb() -> DynamoDBServiceResource:
    return boto3.resource("dynamodb")


@functools.lru_cache(maxsize=None)
def get_sns_client() -> SNSClient:
    return boto3.client("sns")


_matcher = None


def get_matcher(banks_table: BanksTable):
    global _matcher
    if _matcher is None:
        _matcher = Matcher(
            index_bucket_name=INDEXES_BUCKET_NAME,
            supported_signal_types=[PdqSignal, VideoMD5Signal],
            banks_table=banks_table,
        )
    return _matcher


logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    Listens to SQS events fired when new hash is generated. Loads the index
    stored in an S3 bucket and looks for a match.

    When matched, publishes a notification to an SNS endpoint. Note this is in
    contrast with hasher and indexer. They publish to SQS directly. Publishing
    to SQS implies there can be only one consumer.

    Because, here, in the matcher, we publish to SNS, we can plug multiple
    queues behind it and profit!
    """
    table = get_dynamodb().Table(DYNAMODB_TABLE)

    banks_table = BanksTable(
        get_dynamodb().Table(BANKS_TABLE), get_signal_type_mapping()
    )

    for sqs_record in event["Records"]:
        message = json.loads(sqs_record["body"])

        if message.get("Event") == "TestEvent":
            logger.debug("Disregarding Test Event")
            continue

        if not PipelineHashRecord.could_be(message):
            logger.warn(
                "Could not de-serialize message in matcher lambda. Message was %s",
                message,
            )
            continue

        hash_record = PipelineHashRecord.from_sqs_message(
            message, get_signal_type_mapping()
        )
        logger.info(
            "HashRecord for contentId: %s with contentHash: %s",
            hash_record.content_id,
            hash_record.content_hash,
        )

        matches = get_matcher(banks_table).match(
            hash_record.signal_type, hash_record.content_hash
        )
        logger.info("Found %d matches.", len(matches))

        for match in matches:
            get_matcher(banks_table).write_match_record_for_result(
                table=table,
                signal_type=hash_record.signal_type,
                content_hash=hash_record.content_hash,
                content_id=hash_record.content_id,
                match=match,
            )

        for match in matches:
            get_matcher(banks_table).write_signal_if_not_found(
                table=table, signal_type=hash_record.signal_type, match=match
            )

        if len(matches) != 0:
            # Publish all messages together
            get_matcher(banks_table).publish_match_message(
                content_id=hash_record.content_id,
                content_hash=hash_record.content_hash,
                matches=matches,
                sns_client=get_sns_client(),
                topic_arn=MATCHES_TOPIC_ARN,
            )

        metrics.flush()
