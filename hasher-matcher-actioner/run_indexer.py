import os
import logging.config

os.environ[
    "THREAT_EXCHANGE_DATA_BUCKET_NAME"
] = "dipanjanm-hashing-data20210402200425191500000003"
os.environ["THREAT_EXCHANGE_DATA_FOLDER"] = "threat_exchange_data/"
os.environ["INDEXES_BUCKET_NAME"] = "dipanjanm-hashing-data20210402200425191500000003"

# os.environ["CONFIG_TABLE_NAME"] = "dipanjanm-HMAConfig"
# os.environ["DYNAMODB_DATASTORE_TABLE"] = "dipanjanm-HMADataStore"
# os.environ[
#     "THREAT_EXCHANGE_API_TOKEN_SECRET_NAME"
# ] = "threatexchange/dipanjanm_api_tokens"


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

from hmalib.lambdas.unified_indexer import lambda_handler


privacy_group_id = 1234567890
data_updated_event = {
    "Records": [
        {
            "Records": [
                {
                    "s3": {
                        "bucket": {
                            "name": os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"]
                        },
                        "object": {
                            "key": os.environ["THREAT_EXCHANGE_DATA_FOLDER"]
                            + str(privacy_group_id)
                            + ".hash_video_md5.te"
                        },
                    }
                }
            ]
        }
    ]
}

lambda_handler(data_updated_event, None)
