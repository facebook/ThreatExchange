# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import json
import boto3
import typing as t
from dataclasses import dataclass
from mypy_boto3_dynamodb.service_resource import Table

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.meta import (
    get_content_type_for_name,
)

from hmalib.common.logging import get_logger
from hmalib.lambdas.api.submit import (
    submit_content_request_from_s3_object,
    record_content_submission,
    send_submission_to_url_queue,
    SubmitContents3ObjectRequestBody,
    SubmitContentViaURLRequestBody,
)


logger = get_logger(__name__)
dynamodb = boto3.resource("dynamodb")

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
SUBMISSIONS_QUEUE_URL = os.environ["SUBMISSIONS_QUEUE_URL"]


class SNSSubmissionRequestBase:
    """
    Abstract base class for submission request over SNS.
    """

    @classmethod
    def could_be(cls, message: t.Dict) -> bool:
        """
        Check if the required fields for this class are in the message
        Note: it checks if the value exists not if it is valid.
        validation is handled in try_from_message
        """
        ALWAYS_REQUIRED_FIELDS = {"content_id", "content_type"}

        fields = message.keys()
        if not ALWAYS_REQUIRED_FIELDS.issubset(fields):
            return False
        if not cls.get_required_subfields().issubset(fields):
            return False
        return True

    @classmethod
    def try_from_message(cls, message: t.Dict):
        """
        Tries to create a single submission object from an event message.
        raises a ValueError if validation checks fail.
        """
        raise NotImplementedError()

    @classmethod
    def get_required_subfields(cls):
        """
        Set of subfields expected on the submission object.
        """
        return {}

    def submit(
        self,
        dynamodb_table: Table,
        submissions_queue_url: str,
    ):
        """
        Submit this request object to HMA.
        """
        raise NotImplementedError()


@dataclass
class SubmissionRequestViaS3(
    SNSSubmissionRequestBase, SubmitContents3ObjectRequestBody
):
    """
    Submission payload body sent via this topic is expected to be in
    the same form as API request to the /submit/s3/ endpoint.
    This class adds some additional validation to check the values are not empty.
    and handles the specific of submission
    """

    @classmethod
    def try_from_message(cls, message: t.Dict):
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

    @classmethod
    def get_required_subfields(cls):
        return {"bucket_name", "object_key"}

    def submit(
        self,
        dynamodb_table: Table,
        submissions_queue_url: str,
    ):

        # Reminder the following method does the following:
        # - Creates (or updates) the content object for the given content_id
        # - Takes bucket and key -> creates a signed URL -> sends URL to hasher
        submit_content_request_from_s3_object(
            dynamodb_table=dynamodb_table,
            submissions_queue_url=submissions_queue_url,
            bucket=self.bucket_name,
            key=self.object_key,
            content_id=self.content_id,
            content_type=self.content_type,
            additional_fields=set(self.additional_fields)
            if self.additional_fields
            else set(),
            force_resubmit=True,  # without this after first failure/throttle lambda is likely to get stuck in a retry loop.
        )
        logger.info(
            f"Submitted to HMA - id:{self.content_id}, bucket:{self.bucket_name}, key:{self.object_key}"
        )


@dataclass
class SubmissionRequestViaURL(SNSSubmissionRequestBase, SubmitContentViaURLRequestBody):
    """
    Submission payload body sent via this topic is expected to be in
    the same form as API request to the /submit/url/ endpoint.
    This class adds some additional validation to check the values are not empty.
    and handles the specific of submission
    """

    @classmethod
    def try_from_message(cls, message: t.Dict):
        submission = cls(
            content_id=message["content_id"],
            content_type=get_content_type_for_name(message["content_type"]),
            content_url=message["content_url"],
            additional_fields=message.get("additional_fields", []),
        )
        if not submission.content_id or not submission.content_url:
            raise ValueError("Empty string given for required field")
        return submission

    @classmethod
    def get_required_subfields(cls):
        return {"content_url"}

    def submit(
        self,
        dynamodb_table: Table,
        submissions_queue_url: str,
    ):
        content_ref, content_ref_type = self.get_content_ref_details()

        record_content_submission(
            dynamodb_table,
            content_id=self.content_id,
            content_type=self.content_type,
            content_ref=content_ref,
            content_ref_type=content_ref_type,
            additional_fields=set(self.additional_fields)
            if self.additional_fields
            else set(),
            force_resubmit=True,  # without this after first failure/throttle lambda is likely to get stuck in a retry loop.
        )

        send_submission_to_url_queue(
            dynamodb_table=dynamodb_table,
            submissions_queue_url=submissions_queue_url,
            content_id=self.content_id,
            content_type=self.content_type,
            url=self.content_url,
        )
        logger.info(f"Submitted to HMA - id:{self.content_id}, url:{self.content_url}")


def lambda_handler(event, context):
    for sqs_record in event["Records"]:
        try:
            sqs_record_body = json.loads((sqs_record["body"]))
            message = json.loads(sqs_record_body["Message"])
            # It is possble the payload is valid for both submission types
            # in this case we elect to submit via URL as that is the method
            # that does not require additional permissions be given to the lambda.
            if SubmissionRequestViaURL.could_be(message):
                submission = SubmissionRequestViaURL.try_from_message(message)
            elif SubmissionRequestViaS3.could_be(message):
                submission = SubmissionRequestViaS3.try_from_message(message)
            else:
                raise ValueError("Payload missing a required field")
        except ValueError as e:
            logger.exception("Failed to process submit event message.")
            logger.error(sqs_record)
            continue

        # ToDo try catch or deadletter queue to limit retries
        submission.submit(
            dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
            submissions_queue_url=SUBMISSIONS_QUEUE_URL,
        )
