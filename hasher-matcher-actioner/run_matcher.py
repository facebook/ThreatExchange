from datetime import datetime
import json
import os
import uuid
from threatexchange.signal_type.md5 import VideoMD5Signal

os.environ["INDEXES_BUCKET_NAME"] = "dipanjanm-hashing-data20210402200425191500000003"
os.environ["HMA_CONFIG_TABLE"] = "dipanjanm-HMAConfig"
os.environ["DYNAMODB_TABLE"] = "dipanjanm-HMADataStore"
os.environ[
    "MATCHES_TOPIC_ARN"
] = "arn:aws:sns:us-east-1:521978645842:dipanjanm-matches20210402200425219800000003"

import logging.config

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

from hmalib.lambdas.matcher import lambda_handler
from hmalib.common.models.pipeline import PipelineHashRecord

content_id = str(uuid.uuid4())

print(f"Look for content: {content_id}")

hash_message = {
    "Records": [
        {
            "body": json.dumps(
                PipelineHashRecord(
                    content_id=content_id,
                    signal_type=VideoMD5Signal,
                    content_hash="b1aa35aec2a92edeee4397de86a4d7e3",
                    updated_at=datetime.now(),
                    signal_specific_attributes={},
                ).to_sqs_message()
            )
        }
    ]
}

lambda_handler(hash_message, None)
