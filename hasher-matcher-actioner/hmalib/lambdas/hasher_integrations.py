import os
import boto3
import json

from botocore.exceptions import ClientError
from hmalib.common.logging import get_logger
from hmalib.lambdas.api.submit import (
    from_url,
    SubmitContentRequestBody,
    SubmissionType,
    ContentType,
    SubmitContentError,
)
from hmalib.lambdas.pdq.pdq_hasher import lambda_handler as pdq_hasher_lambda_handler

logger = get_logger(__name__)

# DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
# IMAGES_TOPIC_ARN = os.environ["IMAGES_TOPIC_ARN"]
# logger.info("IMAGES_TOPIC_ARN")
# logger.info(IMAGES_TOPIC_ARN)

dynamodb = boto3.resource("dynamodb")


def lambda_handler(event, context):
    logger.info(event)
    if is_s3_event(event):
        return process_s3_event(event)

    return {"result": "Failed to process event. Unknown event type", "event": event}


def is_s3_event(event) -> bool:
    return "Records" in event and all("s3" in record for record in event["Records"])


def process_s3_event(event) -> dict:
    pdq_hasher_event = {
        "Records": [{"body": json.dumps({"Message": json.dumps(event)})}]
    }
    logger.info("pdq_hasher_event")
    logger.info(pdq_hasher_event)

    pdq_hasher_lambda_handler(pdq_hasher_event, None)
    return {
        "result": "Sucessfully sent image to hasher lambda",
        "event": event,
    }

    # for record in event["Records"]:
    #     uploaded_object_key = record["s3"]["object"]["key"]
    #     bucket_name = record["s3"]["bucket"]["name"]
    #     presigned_get_url = create_presigned_get_url(
    #         bucket_name,
    #         uploaded_object_key,
    #     )
    #     if presigned_get_url:
    #         request = SubmitContentRequestBody(
    #             submission_type=SubmissionType.FROM_URL,
    #             content_id=bucket_name + ":" + uploaded_object_key,
    #             content_bytes_url_or_file_type=presigned_get_url,
    #             content_type=ContentType.PHOTO,
    #             additional_fields=[],
    #         )

    # response = from_url(
    #     request, dynamodb.Table(DYNAMODB_TABLE), IMAGES_TOPIC_ARN
    # )

    # if response is SubmitContentError:
    #     return {
    #         "result": "Failed to submit content. " + response.message,
    #         "event": event,
    #     }
    # return {
    #     "result": "Successfully sent s3 event to hasher",
    #     "event": event,
    # }
    # return {
    #     "result": "Failed to create a presigned url for the s3 object",
    #     "event": event,
    # }


def create_presigned_get_url(bucket_name, key, expiration=3600):
    """
    Generate a presigned URL to read an S3 object
    """

    s3_client = boto3.client("s3")
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket_name,
                "Key": key,
            },
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logger.error(e)
        return None

    return response


if __name__ == "__main__":
    event = {
        "Records": [
            {
                "s3": {
                    "object": {"key": "212000.jpg", "size": 500},
                    "bucket": {"name": "jesses-separate-aws-bucket"},
                }
            }
        ]
    }
    print(lambda_handler(event, None))
