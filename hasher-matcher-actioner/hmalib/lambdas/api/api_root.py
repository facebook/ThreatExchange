# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import bottle
import boto3
import json
import typing as t
from apig_wsgi import make_lambda_handler
from bottle import response, error

from hmalib.common.logging import get_logger

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
    get_datasets_api(
        hma_config_table=HMA_CONFIG_TABLE,
        datastore_table=dynamodb.Table(DYNAMODB_TABLE),
        threat_exchange_data_bucket_name=THREAT_EXCHANGE_DATA_BUCKET_NAME,
        threat_exchange_data_folder=THREAT_EXCHANGE_DATA_FOLDER,
        threat_exchange_pdq_file_extension=THREAT_EXCHANGE_PDQ_FILE_EXTENSION,
    ),
)

app.mount("/stats/", get_stats_api(dynamodb_table=dynamodb.Table(DYNAMODB_TABLE)))

app.mount(
    "/actions/",
    get_actions_api(hma_config_table=HMA_CONFIG_TABLE),
)

if __name__ == "__main__":
    app.run()
