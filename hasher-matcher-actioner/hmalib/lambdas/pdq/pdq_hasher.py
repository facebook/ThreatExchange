# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import os
import tempfile
from pathlib import Path
from urllib.parse import unquote_plus
import datetime

import boto3
from mypy_boto3_dynamodb import DynamoDBServiceResource
from threatexchange.hashing import pdq_hasher

from hmalib import metrics
from hmalib.dto import PipelinePDQHashRecord
from hmalib.common import get_logger

logger = get_logger(__name__)
s3_client = boto3.client("s3")
sqs_client = boto3.client("sqs")
dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")

OUTPUT_QUEUE_URL = os.environ["PDQ_HASHES_QUEUE_URL"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]


def lambda_handler(event, context):
    """
    Listens to SQS events generated when new files are added to S3. Downloads
    files to temp-storage, generates PDQ hash and quality from the file.

    Saves hash output to dynamodb.

    Sends a message on an output queue.

    Note: Lambdas have pretty strong tempfile storage limits (512MB as of this
    writing) [1]. We are using the tempfile module in a context manager block,
    so the file gets deleted after use. If additional files are created, ensure
    they are inside their own context managers otherwise the lambda can run out
    of disk-space.

    1: https://docs.aws.amazon.com/lambda/latest/dg/images-create.html
    """
    records_table = dynamodb.Table(DYNAMODB_TABLE)

    for sqs_record in event["Records"]:
        sns_notification = json.loads(sqs_record["body"])
        message = json.loads(sns_notification["Message"])

        if message.get("Event") == "s3:TestEvent":
            logger.info("Disregarding S3 Test Event")
            continue

        for s3_record in message["Records"]:
            bucket_name = s3_record["s3"]["bucket"]["name"]
            key = unquote_plus(s3_record["s3"]["object"]["key"])

            # Ignore Folders and Empty Files
            if s3_record["s3"]["object"]["size"] == 0:
                logger.info("Disregarding empty file or directory: %s", key)
                continue

            logger.info("generating pdq hash for %s/%s", bucket_name, key)

            with metrics.timer(metrics.names.pdq_hasher_lambda.download_file):
                bytes_: bytes = s3_client.get_object(Bucket=bucket_name, Key=key)[
                    "Body"
                ].read()

            with metrics.timer(metrics.names.pdq_hasher_lambda.hash):
                pdq_hash, quality = pdq_hasher.pdq_from_bytes(bytes_)

            hash_record = PipelinePDQHashRecord(
                key, pdq_hash, datetime.datetime.now(), quality
            )

            hash_record.write_to_table(records_table)

            # Publish to SQS queue
            sqs_client.send_message(
                QueueUrl=OUTPUT_QUEUE_URL,
                MessageBody=json.dumps(hash_record.to_sqs_message()),
            )

            logger.info("Published new PDQ hash")

    metrics.flush()
