# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import os
import datetime
import typing as t

import boto3
from mypy_boto3_dynamodb import DynamoDBServiceResource
from threatexchange.hashing import pdq_hasher

from hmalib import metrics
from hmalib.models import PipelinePDQHashRecord
from hmalib.common.message_models import (
    S3ImageSubmission,
    S3ImageSubmissionBatchMessage,
    URLImageSubmissionMessage,
)
from hmalib.common.logging import get_logger
from hmalib.common.image_sources import URLImageSource, S3BucketImageSource

logger = get_logger(__name__)
sqs_client = boto3.client("sqs")
dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")

OUTPUT_QUEUE_URL = os.environ["PDQ_HASHES_QUEUE_URL"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
IMAGE_FOLDER_KEY = os.environ[
    "IMAGE_FOLDER_KEY"
]  # Misnamed, this is a prefix, not a key, if renaming, use IMAGE_PREFIX


def get_image_bytes(
    submission_message: t.Union[URLImageSubmissionMessage, S3ImageSubmission],
    default_s3_bucket_image_prefix: str,
):
    """
    Takes a submission_message, identifies how best to get its bytes. Future
    work on re-using sessions for `requests` or any possible optimization must
    go here.

    Once we have more hashing lambdas that need access to media, this could be
    moved into its own module.
    """
    if isinstance(submission_message, URLImageSubmissionMessage):
        return URLImageSource().get_image_bytes(submission_message.url)
    else:
        return S3BucketImageSource(
            submission_message.bucket, default_s3_bucket_image_prefix
        ).get_image_bytes(submission_message.content_id)


def lambda_handler(event, context):
    """
    Listens to SQS events generated when new files are added to S3. Downloads
    files to temp-storage, generates PDQ hash and quality from the file.

    The SQS events could be from S3 or directly from the Submission API lambdas
    in case of a URL submission.

    Saves hash output to dynamodb.

    Sends a message on an output queue.

    Note: The image is brought into memory and then handed over to the hasher.
    If you are hashing large images, you may need to increase the memory
    allocated to the lambda. Also remember that images that look small on disk
    (eg. low quality jpegs) still occupy a lot of space in memory. The
    pixel-size of the image is a better indicator of the space it will take in
    memory.
    """
    records_table = dynamodb.Table(DYNAMODB_TABLE)

    for sqs_record in event["Records"]:
        message_body = json.loads(sqs_record["body"])
        message = json.loads(message_body["Message"])

        if message.get("Event") == "s3:TestEvent":
            logger.info("Disregarding S3 Test Event")
            continue

        images_to_process: t.List[
            t.Union[URLImageSubmissionMessage, S3ImageSubmission]
        ] = []

        if URLImageSubmissionMessage.could_be(message):
            images_to_process.append(
                URLImageSubmissionMessage.from_sqs_message(message)
            )
        elif S3ImageSubmissionBatchMessage.could_be(message):
            images_to_process.extend(
                S3ImageSubmissionBatchMessage.from_sqs_message(
                    message, image_prefix=IMAGE_FOLDER_KEY
                ).image_submissions
            )
        else:
            logger.warn(
                "PDQ Hahser could not process incoming message %s", repr(message)
            )

        for image in images_to_process:
            logger.info("Getting bytes for submission:  %s", repr(image))
            with metrics.timer(metrics.names.pdq_hasher_lambda.download_file):
                bytes_: bytes = get_image_bytes(image, IMAGE_FOLDER_KEY)

            logger.info("Generating PDQ hash for submission: %s", repr(image))

            with metrics.timer(metrics.names.pdq_hasher_lambda.hash):
                pdq_hash, quality = pdq_hasher.pdq_from_bytes(bytes_)

            hash_record = PipelinePDQHashRecord(
                image.content_id, pdq_hash, datetime.datetime.now(), quality
            )

            hash_record.write_to_table(records_table)

            # Publish to SQS queue
            sqs_client.send_message(
                QueueUrl=OUTPUT_QUEUE_URL,
                MessageBody=json.dumps(hash_record.to_sqs_message()),
            )

            logger.info("Published new PDQ hash")

    metrics.flush()
