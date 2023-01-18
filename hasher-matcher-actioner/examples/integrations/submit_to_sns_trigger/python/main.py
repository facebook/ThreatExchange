# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import json
import boto3


SUBMIT_TOPIC_ARN = os.environ["SUBMIT_TOPIC_ARN"]


def lambda_handler(event, context):
    sns_client = boto3.client("sns")
    print(event)
    payload = event.get("payload")
    if event:
        sns_client.publish(TopicArn=SUBMIT_TOPIC_ARN, Message=json.dumps(payload))
        return {"result": json.dumps(payload)}
    else:
        return {"result": "error: missing submission payload"}


if __name__ == "__main__":
    event = {
        "payload": {
            "content_id": "example-submission-id-1",
            "content_type": "photo",
            "additional_fields": ["submitted_via_manual_use_of_python_lambda"],
            "bucket_name": "example-test-media",
            "object_key": "images/abc123.jpg",
        }
    }
    lambda_handler(event, None)
