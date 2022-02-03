# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import bottle
import boto3
import json
import typing as t
from apig_wsgi import make_lambda_handler
from bottle import response, error
from mypy_boto3_dynamodb.service_resource import Table

from hmalib.common.logging import get_logger
from hmalib.common.models.content import ContentRefType, ContentType

from hmalib.lambdas.api.bank import get_bank_api
from hmalib.lambdas.api.action_rules import get_action_rules_api
from hmalib.lambdas.api.actions import get_actions_api
from hmalib.lambdas.api.content import get_content_api
from hmalib.lambdas.api.datasets import get_datasets_api
from hmalib.lambdas.api.indexes import get_indexes_api
from hmalib.lambdas.api.matches import get_matches_api
from hmalib.lambdas.api.stats import get_stats_api
from hmalib.lambdas.api.submit import (
    get_submit_api,
    create_presigned_url,
    submit_content_request_from_s3_object,
)

# Set to 10MB for images
bottle.BaseRequest.MEMFILE_MAX = 10 * 1024 * 1024

app = bottle.default_app()
apig_wsgi_handler = make_lambda_handler(app)

logger = get_logger(__name__)

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

THREAT_EXCHANGE_DATA_BUCKET_NAME = os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"]
THREAT_EXCHANGE_DATA_FOLDER = os.environ["THREAT_EXCHANGE_DATA_FOLDER"]
HMA_CONFIG_TABLE = os.environ["HMA_CONFIG_TABLE"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
BANKS_TABLE = os.environ["BANKS_TABLE"]
COUNTS_TABLE_NAME = os.environ["COUNTS_TABLE_NAME"]
BANKS_MEDIA_BUCKET_NAME = os.environ["BANKS_MEDIA_BUCKET_NAME"]
IMAGE_BUCKET_NAME = os.environ["IMAGE_BUCKET_NAME"]
IMAGE_PREFIX = os.environ["IMAGE_PREFIX"]
SUBMISSIONS_QUEUE_URL = os.environ["SUBMISSIONS_QUEUE_URL"]
HASHES_QUEUE_URL = os.environ["HASHES_QUEUE_URL"]

INDEXES_BUCKET_NAME = os.environ["INDEXES_BUCKET_NAME"]
INDEXER_FUNCTION_NAME = os.environ["INDEXER_FUNCTION_NAME"]
WRITEBACK_QUEUE_URL = os.environ["WRITEBACKS_QUEUE_URL"]

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


@app.get("/root/")
def root():
    """
    root endpoint to make sure the API is live and check when it was last updated
    """
    context = bottle.request.environ.get("apig_wsgi.context")
    invoked_function_arn = context.invoked_function_arn
    client = boto3.client("lambda")
    last_modified = client.get_function_configuration(
        FunctionName=invoked_function_arn
    )["LastModified"]

    return {
        "message": "Welcome to the HMA API!",
        "last_modified": last_modified,
    }


def lambda_handler(event, context):
    """
    This lambda is invoked in 2 situations:

    1. When the API is called, it uses bottle to process the request and send it to the direct function

    2. Platforms can connect their AWS S3 Buckets directly to HMA so that uploads to those buckets are
    fed directly into the system. When an upload occurs, this lambda is invoked with an s3 event. We then
    convert the event into a URL which we submit to the hasher (via SNS)

    TODO refactor #2 to its own lambda that handles more general sqs events
    """
    if is_s3_event(event):
        logger.info(
            "Lambda triggered with S3 event. Converting to submit content request."
        )
        return process_s3_event(event)

    response = apig_wsgi_handler(event, context)
    return response


def is_s3_event(event: dict) -> bool:
    return "Records" in event and all("s3" in record for record in event["Records"])


def process_s3_event(event: dict) -> None:
    for record in event["Records"]:
        record = record["s3"]
        if record["object"]["size"] == 0:
            # ignore folders and empty files
            continue
        bucket: str = record["bucket"]["name"]
        key: str = record["object"]["key"]
        submit_content_request_from_s3_object(
            dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
            submissions_queue_url=SUBMISSIONS_QUEUE_URL,
            bucket=bucket,
            key=key,
        )
        logger.info(f"Sucessfully submitted s3 event record as url upload.")


app.mount(
    "/action-rules/",
    get_action_rules_api(hma_config_table=HMA_CONFIG_TABLE),
)

app.mount(
    "/matches/",
    get_matches_api(
        datastore_table=dynamodb.Table(DYNAMODB_TABLE),
        hma_config_table=HMA_CONFIG_TABLE,
        indexes_bucket_name=INDEXES_BUCKET_NAME,
        writeback_queue_url=WRITEBACK_QUEUE_URL,
        bank_table=dynamodb.Table(BANKS_TABLE),
    ),
)

app.mount(
    "/content/",
    get_content_api(
        dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
        image_bucket=IMAGE_BUCKET_NAME,
        image_prefix=IMAGE_PREFIX,
    ),
)

app.mount(
    "/submit/",
    get_submit_api(
        dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
        image_bucket=IMAGE_BUCKET_NAME,
        image_prefix=IMAGE_PREFIX,
        submissions_queue_url=SUBMISSIONS_QUEUE_URL,
        hash_queue_url=HASHES_QUEUE_URL,
    ),
)

app.mount(
    "/datasets/",
    get_datasets_api(
        hma_config_table=HMA_CONFIG_TABLE,
        datastore_table=dynamodb.Table(DYNAMODB_TABLE),
        threat_exchange_data_bucket_name=THREAT_EXCHANGE_DATA_BUCKET_NAME,
        threat_exchange_data_folder=THREAT_EXCHANGE_DATA_FOLDER,
    ),
)

app.mount("/stats/", get_stats_api(counts_table=dynamodb.Table(COUNTS_TABLE_NAME)))

app.mount(
    "/actions/",
    get_actions_api(hma_config_table=HMA_CONFIG_TABLE),
)

app.mount(
    "/banks/",
    get_bank_api(
        bank_table=dynamodb.Table(BANKS_TABLE),
        bank_user_media_bucket=BANKS_MEDIA_BUCKET_NAME,
        submissions_queue_url=SUBMISSIONS_QUEUE_URL,
    ),
)

app.mount(
    "/indexes/",
    get_indexes_api(
        indexes_bucket_name=INDEXES_BUCKET_NAME,
        indexer_function_name=INDEXER_FUNCTION_NAME,
    ),
)

if __name__ == "__main__":
    app.run()
