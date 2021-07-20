import os
import json
import boto3

from hmalib.common.logging import get_logger

logger = get_logger(__name__)

sqs_client = boto3.client("sqs")

PDQ_IMAGES_QUEUE_URL = os.environ["PDQ_IMAGES_QUEUE_URL"]


def lambda_handler(event, context):
    if is_s3_event(event):
        return process_s3_event(event)

    return {"result": "Failed to process event. Unknown event type", "event": event}


def is_s3_event(event) -> bool:
    return "Records" in event and all("s3" in record for record in event["Records"])


def process_s3_event(event) -> dict:
    logger.info(event)

    event["local_bucket"] = True
    sqs_client.send_message(
        QueueUrl=PDQ_IMAGES_QUEUE_URL,
        MessageBody=json.dumps({"Message": json.dumps(event)}),
    )

    return {
        "result": "Sucessfully sent image to hasher sqs queue",
        "event": event,
    }


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
