import os

import boto3

from hmalib.common.logging import get_logger
from hmalib.lambdas.api.submit import (
    record_content_submission,
    SubmitContentRequestBody,
    SubmissionType,
    create_presigned_get_url,
)

logger = get_logger(__name__)

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
dynamodb = boto3.resource("dynamodb")


def lambda_handler(event, context):

    for record in event["Records"]:
        uploaded_object_key = record["s3"]["object"]["key"]
        bucket_name = record["s3"]["bucket"]["name"]


        request = SubmitContentRequestBody(
            submission_type=SubmissionType.FROM_URL,
            content_id=bucket_name + ":" + uploaded_object_key,
            content_bytes_url_or_file_type=create_presigned_get_url(
                bucket_name,
                uploaded_object_key,
                None,
            ),
        )
        table = (dynamodb.Table(DYNAMODB_TABLE),)
        record_content_submission(table, request)


if __name__ == "__main__":
    event = {
        "Records": [
            {
                "s3": {
                    "object": {"key": "212000.jpg"},
                    "bucket": {
                        "name": "jesses-separate-aws-bucket",
                    },
                }
            }
        ]
    }
    lambda_handler(event)
