# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import logging
import os
import tempfile
from pathlib import Path
from urllib.parse import unquote_plus

import boto3
from threatexchange.hashing import pdq_hasher

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
sqs_client = boto3.client("sqs")


def lambda_handler(event, context):
    OUTPUT_QUEUE_URL = os.environ["PDQ_HASHES_QUEUE_URL"]
    for sqs_record in event["Records"]:
        sns_notification = json.loads(sqs_record["body"])
        message = json.loads(sns_notification["Message"])
        if message.get("Event") == "s3:TestEvent":
            logger.info("Disregarding S3 Test Event")
            continue
        for s3_record in message["Records"]:
            # Ignore Folders and Empty Files
            bucket_name = s3_record["s3"]["bucket"]["name"]
            key = unquote_plus(s3_record["s3"]["object"]["key"])
            if s3_record["s3"]["object"]["size"] == 0:
                logger.info("Disregarding empty file or directory: %s", key)
                continue
            logger.info("generating pdq hash for %s/%s", bucket_name, key)
            with tempfile.NamedTemporaryFile() as tmp_file:
                path = Path(tmp_file.name)
                s3_client.download_fileobj(bucket_name, key, tmp_file)
                pdq_hash, quality = pdq_hasher.pdq_from_file(path)
                output = {"hash": pdq_hash, "type": "pdq", "key": key}
                logger.info("publishing new pdq hash")
                sqs_client.send_message(
                    QueueUrl=OUTPUT_QUEUE_URL,
                    MessageBody=json.dumps(output),
                )
