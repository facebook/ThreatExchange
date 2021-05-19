# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import traceback
import bottle
import boto3
import json
import base64
import datetime
import typing as t
from apig_wsgi import make_lambda_handler
from bottle import response, error

from hmalib import metrics
from hmalib.common.logging import get_logger
from hmalib.common.s3_adapters import ThreatExchangeS3PDQAdapter, S3ThreatDataConfig

from .action_rules_api import get_action_rules_api
from .actions_api import get_actions_api
from .content import get_content_api
from .datasets_api import get_datasets_api
from .matches import get_matches_api
from .stats import get_stats_api
from .submit import get_submit_api

# Set to 10MB for images
bottle.BaseRequest.MEMFILE_MAX = 10 * 1024 * 1024

app = bottle.default_app()
apig_wsgi_handler = make_lambda_handler(app)

logger = get_logger(__name__)

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

THREAT_EXCHANGE_DATA_BUCKET_NAME = os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"]
THREAT_EXCHANGE_DATA_FOLDER = os.environ["THREAT_EXCHANGE_DATA_FOLDER"]
THREAT_EXCHANGE_PDQ_FILE_EXTENSION = os.environ["THREAT_EXCHANGE_PDQ_FILE_EXTENSION"]
HMA_CONFIG_TABLE = os.environ["HMA_CONFIG_TABLE"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
IMAGE_BUCKET_NAME = os.environ["IMAGE_BUCKET_NAME"]
IMAGE_FOLDER_KEY = os.environ["IMAGE_FOLDER_KEY"]

# Override common errors codes to return json instead of bottle's default html
@error(404)
def error404(e):
    logger.error(f"{e}")
    response.content_type = "application/json"
    return json.dumps({"error": "404"})


@error(405)
def error405(e):
    logger.error(f"{e}")
    response.content_type = "application/json"
    return json.dumps({"error": "405"})


@error(500)
def error500(e):
    logger.exception("Exception raised", exc_info=e.exception)
    response.content_type = "application/json"
    return json.dumps({"error": "500"})


@app.get("/")
def root():
    return {
        "message": "Hello World, HMA",
    }


@app.get("/signals")
def signals():
    """
    Summary of all signal sources
    """
    return {"signals": get_signals()}


@app.get("/hash-counts")
def hash_count():
    """
    how many hashes exist in HMA
    """
    results = get_signal_hash_count()
    logger.debug(results)
    hash_counts = {
        name.replace(THREAT_EXCHANGE_PDQ_FILE_EXTENSION, "").replace(
            THREAT_EXCHANGE_DATA_FOLDER, ""
        ): value
        for name, value in results.items()
    }
    return hash_counts if hash_counts else {}


def lambda_handler(event, context):
    """
    root request handler
    """
    response = apig_wsgi_handler(event, context)
    return response


class SignalSourceType(t.TypedDict):
    type: str
    count: int


class SignalSourceSummary(t.TypedDict):
    name: str
    signals: t.List[SignalSourceType]
    updated_at: str


def get_signals() -> t.List[SignalSourceSummary]:
    """
    TODO this should be updated to check ThreatExchangeConfig
    based on what it finds in the config it should then do a s3 select on the files
    """
    signals = []
    counts = get_signal_hash_count()
    for dataset, total in counts.items():
        if dataset.endswith(THREAT_EXCHANGE_PDQ_FILE_EXTENSION):
            dataset_name = dataset.replace(
                THREAT_EXCHANGE_PDQ_FILE_EXTENSION, ""
            ).replace(THREAT_EXCHANGE_DATA_FOLDER, "")
            signals.append(
                SignalSourceSummary(
                    name=dataset_name,
                    # TODO remove hardcode and config mapping file extention to type
                    signals=[SignalSourceType(type="HASH_PDQ", count=total[0])],
                    updated_at="TODO",
                )
            )
    return signals


# TODO this method is expensive some cache or memoization method might be a good idea.
def get_signal_hash_count() -> t.Dict[str, t.Tuple[int, str]]:
    s3_config = S3ThreatDataConfig(
        threat_exchange_data_bucket_name=THREAT_EXCHANGE_DATA_BUCKET_NAME,
        threat_exchange_data_folder=THREAT_EXCHANGE_DATA_FOLDER,
        threat_exchange_pdq_file_extension=THREAT_EXCHANGE_PDQ_FILE_EXTENSION,
    )
    pdq_storage = ThreatExchangeS3PDQAdapter(
        config=s3_config, metrics_logger=metrics.names.api_hash_count()
    )
    pdq_data_files = pdq_storage.load_data()
    return {
        file_name: (len(rows), pdq_storage.last_modified[file_name])
        for file_name, rows in pdq_data_files.items()
    }


app.mount(
    "/action-rules/",
    get_action_rules_api(hma_config_table=HMA_CONFIG_TABLE),
)

app.mount(
    "/matches/",
    get_matches_api(
        dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
        image_folder_key=IMAGE_FOLDER_KEY,
        hma_config_table=HMA_CONFIG_TABLE,
    ),
)

app.mount(
    "/content/",
    get_content_api(
        dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
        image_bucket_key=IMAGE_BUCKET_NAME,
        image_folder_key=IMAGE_FOLDER_KEY,
    ),
)

app.mount(
    "/submit/",
    get_submit_api(
        dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
        image_bucket_key=IMAGE_BUCKET_NAME,
        image_folder_key=IMAGE_FOLDER_KEY,
    ),
)

app.mount(
    "/datasets/",
    get_datasets_api(hma_config_table=HMA_CONFIG_TABLE),
)

app.mount("/stats/", get_stats_api(dynamodb_table=dynamodb.Table(DYNAMODB_TABLE)))

app.mount(
    "/actions/",
    get_actions_api(hma_config_table=HMA_CONFIG_TABLE),
)

if __name__ == "__main__":
    app.run()
