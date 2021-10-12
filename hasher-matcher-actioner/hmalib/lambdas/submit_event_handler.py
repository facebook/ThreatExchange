# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import json
import boto3
import typing as t
from dataclasses import dataclass

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.meta import (
    get_content_type_for_name,
)

from hmalib.common.logging import get_logger
from hmalib.lambdas.api.submit import (
    submit_content_request_from_s3_object,
    SubmitContents3ObjectRequestBody,
)


logger = get_logger(__name__)
dynamodb = boto3.resource("dynamodb")

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
SUBMISSIONS_QUEUE_URL = os.environ["SUBMISSIONS_QUEUE_URL"]


@dataclass
class SubmissionRequest(SubmitContents3ObjectRequestBody):
    """
    Submission payload body sent via this topic is expected to be in
    the same form as API request to the /submit/s3/ endpoint
    with some additional validation to check the values are not empty.
    """

    @classmethod
    def try_from_messsage(cls, message: t.Dict):
        """try to create a submission from an event message"""
        submission = cls(
            content_id=message["content_id"],
            content_type=get_content_type_for_name(message["content_type"]),
            bucket_name=message["bucket_name"],
            object_key=message["object_key"],
            additional_fields=message.get("additional_fields", []),
        )
        if (
            not submission.content_id
            or not submission.bucket_name
            or not submission.object_key
        ):
            raise ValueError("Empty string given for required field")
        return submission


def lambda_handler(event, context):
    for sqs_record in event["Records"]:
        try:
            sqs_record_body = json.loads((sqs_record["body"]))
            message = json.loads(sqs_record_body["Message"])
            submission = SubmissionRequest.try_from_messsage(message)
        except ValueError as e:
            logger.info("Failed to process submit event message.")
            logger.error(sqs_record)
            # Logging as exceptions could cause the lambda to retry.
            # We want to avoid this because it will just fail again and
            # also trigger a resubmit for the other events/messages
            logger.info(e)
            continue

        # Reminder the following method does the following:
        # - Creates (or updates) the content object for the given content_id
        # - Takes bucket and key -> creates a signed URL -> sends URL to hasher
        submit_content_request_from_s3_object(
            dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
            submissions_queue_url=SUBMISSIONS_QUEUE_URL,
            bucket=submission.bucket_name,
            key=submission.object_key,
            content_id=submission.content_id,
            content_type=submission.content_type,
            additional_fields=set(submission.additional_fields),
            force_resubmit=True,  # without this after first failure/throttle lambda is likely to get stuck in a retry loop.
        )
        logger.info(
            f"Submitted to HMA - id:{submission.content_id}, bucket:{submission.bucket_name}, key:{submission.object_key}"
        )
