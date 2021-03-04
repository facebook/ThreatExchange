# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import logging
import os
import tempfile
from pathlib import Path
from urllib.parse import unquote_plus
import datetime

import boto3
from mypy_boto3_dynamodb import DynamoDBServiceResource
from threatexchange.hashing import pdq_hasher

from hmalib.dto import PDQHashRecord
from hmalib.storage.hashstore import HashStore
from hmalib import metrics

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
    store = HashStore(records_table)

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
            with tempfile.NamedTemporaryFile() as tmp_file:
                path = Path(tmp_file.name)
                with metrics.timer(metrics.names.pdq_hasher_lambda.download_file):
                    s3_client.download_fileobj(bucket_name, key, tmp_file)

                with metrics.timer(metrics.names.pdq_hasher_lambda.hash):
                    pdq_hash, quality = pdq_hasher.pdq_from_file(path)

                hash_record = PDQHashRecord(
                    key, pdq_hash, quality, datetime.datetime.now()
                )

                # Add to dynamodb hash store
                store.add_hash(hash_record)

                # Publish to SQS queue
                sqs_client.send_message(
                    QueueUrl=OUTPUT_QUEUE_URL,
                    MessageBody=json.dumps(hash_record.to_sqs_message()),
                )

                logger.info("Published new PDQ hash")

    metrics.flush()
