import os
import json
import uuid
import logging.config

os.environ["DYNAMODB_TABLE"] = "dipanjanm-HMADataStore"
os.environ["BANKS_TABLE"] = "dipanjanm-HMABanks"
os.environ["HMA_CONFIG_TABLE"] = "dipanjanm-HMAConfig"
os.environ[
    "IMAGES_TOPIC_ARN"
] = "arn:aws:sns:us-east-1:521978645842:dipanjanm-images20210402200424208000000001"
os.environ["IMAGE_BUCKET_NAME"] = "dipanjanm-hashing-data20210402200425191500000003"
os.environ["IMAGE_PREFIX"] = "images/"
os.environ["MEASURE_PERFORMANCE"] = "True"
os.environ[
    "SUBMISSIONS_QUEUE_URL"
] = "https://sqs.us-east-1.amazonaws.com/521978645842/dipanjanm-submissions20210810131233483300000001"
os.environ[
    "THREAT_EXCHANGE_API_TOKEN_SECRET_NAME"
] = "threatexchange/dipanjanm_api_tokens"
os.environ[
    "THREAT_EXCHANGE_DATA_BUCKET_NAME"
] = "dipanjanm-hashing-data20210402200425191500000003"
os.environ["THREAT_EXCHANGE_DATA_FOLDER"] = "threat_exchange_data/"
os.environ["THREAT_EXCHANGE_PDQ_FILE_EXTENSION"] = ".pdq.te"
os.environ[
    "WRITEBACKS_QUEUE_URL"
] = "https://sqs.us-east-1.amazonaws.com/521978645842/dipanjanm-writebacks20210507214218260500000002"
os.environ[
    "HASHES_QUEUE_URL"
] = "https://sqs.us-east-1.amazonaws.com/521978645842/dipanjanm-submissions20210810131233483300000001"
os.environ["INDEXES_BUCKET_NAME"] = "dipanjanm-hashing-data20210402200425191500000003"
os.environ[
    "BANKS_MEDIA_BUCKET_NAME"
] = "dipanjanm-banks-media-20210917142853280100000001"

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

from hmalib.lambdas.api.api_root import app

app.run()
