import os
import json
import uuid
import logging.config

from threatexchange.content_type.photo import PhotoContent

from hmalib.common.message_models import URLSubmissionMessage

os.environ[
    "HASHES_QUEUE_URL"
] = "https://sqs.us-east-1.amazonaws.com/521978645842/dipanjanm-pdq-images20210402200424208300000001"
os.environ["DYNAMODB_TABLE"] = "dipanjanm-HMADataStore"


LOGGING = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

logging.config.dictConfig(LOGGING)

from hmalib.lambdas.hashing import lambda_handler

content_id = str(uuid.uuid4())
print(f"Will use content_id: {content_id}")


submission_message = {
    "Records": [
        {
            "body": json.dumps(
                URLSubmissionMessage(
                    content_type=PhotoContent,
                    content_id=content_id,
                    url="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png",
                ).to_sqs_message()
            )
        }
    ]
}

lambda_handler(submission_message, None)
