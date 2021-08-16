# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import bottle
import boto3
import json
import typing as t
from apig_wsgi import make_lambda_handler
from bottle import response, error
from uuid import uuid4
from mypy_boto3_dynamodb.service_resource import Table

from threatexchange.content_type.photo import PhotoContent

from hmalib.common.logging import get_logger
from hmalib.common.content_models import ContentRefType, ContentType

from .action_rules_api import get_action_rules_api
from .actions_api import get_actions_api
from .content import get_content_api
from .datasets_api import get_datasets_api
from .matches import get_matches_api
from .stats import get_stats_api
from .submit import (
    get_submit_api,
    create_presigned_url,
    record_content_submission,
    send_submission_to_url_queue,
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
THREAT_EXCHANGE_PDQ_FILE_EXTENSION = os.environ["THREAT_EXCHANGE_PDQ_FILE_EXTENSION"]
HMA_CONFIG_TABLE = os.environ["HMA_CONFIG_TABLE"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
IMAGE_BUCKET_NAME = os.environ["IMAGE_BUCKET_NAME"]
IMAGE_FOLDER_KEY = os.environ[
    "IMAGE_FOLDER_KEY"
]  # Misnamed, this is a prefix, not a key, if renaming, use IMAGE_PREFIX
SUBMISSIONS_QUEUE_URL = os.environ["SUBMISSIONS_QUEUE_URL"]

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
    This lambda is invoked in 2 situations:

    1. When the API is called, it uses bottle to process the request and send it to the direct function

    2. Platforms can connect their AWS S3 Buckets directly to HMA so that uploads to those buckets are
    fed directly into the system. When an upload occurs, this lambda is invoked with an s3 event. We then
    convert the event into a URL which we submit to the hasher (via SNS)
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
        submit_content_request_from_s3_event_record(
            record,
            dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
            submissions_queue_url=SUBMISSIONS_QUEUE_URL,
        )
        logger.info(f"Sucessfully submitted s3 event record as url upload.")


def submit_content_request_from_s3_event_record(
    record: dict,
    dynamodb_table: Table,
    submissions_queue_url: str,
):
    """
    Converts s3 event into a ContentObject and url_submission_message using helpers
    from submit.py

    For partner bucket uploads, the content IDs are unique and (somewhat) readable but
    not reversable
      * uniqueness is provided by uuid4 which has a collision rate of 2^-36
      * readability is provided by including part of the key in the content id
      * modifications to the key mean that the original content bucket and key are
        not derivable from the content ID alone

    The original content (bucket and key) is stored in the reference url which is passed
    to the webhook via additional_fields

    Q: Why not include full key and bucket in content_id?
    A: Bucket keys often have "/" which dont work well with ContentDetails UI page
    """
    bucket: str = record["bucket"]["name"]
    key: str = record["object"]["key"]

    readable_key = key.split("/")[-1].replace("?", ".").replace("&", ".")
    content_id = f"{uuid4()}-{readable_key}"

    presigned_url = create_presigned_url(bucket, key, None, 3600, "get_object")
    reference_url = f"https://{bucket}.s3.amazonaws.com/{key}"

    record_content_submission(
        dynamodb_table,
        content_id,
        PhotoContent,
        content_ref=presigned_url,
        content_ref_type=ContentRefType.URL,
        additional_fields={f"partner_s3_reference_url:{reference_url}"},
    )
    send_submission_to_url_queue(
        dynamodb_table, submissions_queue_url, content_id, PhotoContent, presigned_url
    )


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
        hma_config_table=HMA_CONFIG_TABLE,
    ),
)

app.mount(
    "/content/",
    get_content_api(
        dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
        image_bucket=IMAGE_BUCKET_NAME,
        image_prefix=IMAGE_FOLDER_KEY,
    ),
)

app.mount(
    "/submit/",
    get_submit_api(
        dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
        image_bucket=IMAGE_BUCKET_NAME,
        image_prefix=IMAGE_FOLDER_KEY,
        submissions_queue_url=SUBMISSIONS_QUEUE_URL,
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
