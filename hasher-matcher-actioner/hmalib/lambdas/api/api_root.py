# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
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
from hmalib.models import (
    PDQMatchRecord,
    PipelinePDQHashRecord,
    PDQRecordBase,
)
from hmalib.models import PipelinePDQHashRecord

from .matches import get_matches_api
from .datasets_api import get_datasets_api
from .submit import get_submit_api

# Set to 10MB for /upload
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
IMAGE_FOLDER_KEY_LEN = len(IMAGE_FOLDER_KEY)

# Override common errors codes to return json instead of bottle's default html
@error(404)
def error404(error):
    response.content_type = "application/json"
    return json.dumps({"error": "404"})


@error(405)
def error405(error):
    response.content_type = "application/json"
    return json.dumps({"error": "405"})


@error(500)
def error500(error):
    response.content_type = "application/json"
    return json.dumps({"error": "500"})


@app.get("/")
def root():
    return {
        "message": "Hello World, HMA",
    }


@app.route("/upload", method="POST")
def upload():
    """
    upload API endpoint
    expects request in the format
    {
        fileName: str,
        fileContentsBase64Encoded: bytes,
    }
    """
    fileNameAndEncodedContent = bottle.request.json
    fileName = fileNameAndEncodedContent.get("fileName", None)
    fileContentsBase64Encoded = fileNameAndEncodedContent.get(
        "fileContentsBase64Encoded", None
    )
    fileContents = base64.b64decode(fileContentsBase64Encoded)
    # TODO a whole bunch of validation and error checking...
    s3_client.put_object(
        Body=fileContents,
        Bucket=IMAGE_BUCKET_NAME,
        Key=f"{IMAGE_FOLDER_KEY}{fileName}",
    )

    return {
        "message": "uploaded!",
    }


@app.get("/image/<key>")
def image(key=None):
    """
    return the bytes of an image in the "IMAGE_FOLDER_KEY" based on key
    """
    logger.info(key)
    if not key:
        return
    # TODO a whole bunch of validation and error checking...
    bytes_: bytes = s3_client.get_object(
        Bucket=IMAGE_BUCKET_NAME, Key=f"{IMAGE_FOLDER_KEY}{key}"
    )["Body"].read()
    # TODO make the content type dynamic
    response.set_header("Content-type", "image/jpeg")
    return bytes_


@app.get("/hash/<key>")
def hashes(key=None):
    """
    hash details API endpoint:
    return format: HashResult
    """
    results = get_hash(key)
    logger.debug(results)
    return results if results else {}


@app.get("/signals")
def signals():
    """
    Summary of all signal sources
    """
    return {"signals": get_signals()}


# there is likely a fancy python way to generalize these similar methods
@app.get("/dashboard-hashes")
def dashboard_hashes():
    return {"dashboard-hashes": get_dashboard_hashes()}


@app.get("/dashboard-matches")
def dashboard_matches():
    return {"dashboard-matches": get_dashboard_matches()}


@app.get("/dashboard-signals")
def dashboard_signals():
    return {"dashboard-signals": get_dashboard_signals()}


@app.get("/dashboard-actions")
def dashboard_actions():
    return {"dashboard-actions": get_dashboard_actions()}


@app.get("/dashboard-status")
def dashboard_status():
    return {"dashboard-status": get_dashboard_system_status()}


@app.get("/hash-counts")
def hash_count():
    """
    how many hashes exist in HMA
    """
    results = get_signal_hash_count()
    logger.debug(results)
    return results if results else {}


def lambda_handler(event, context):
    """
    root request handler
    """
    logger.info("Received event: " + json.dumps(event, indent=2))
    response = apig_wsgi_handler(event, context)
    logger.info("Response event: " + json.dumps(response, indent=2))
    return response


class HashResult(t.TypedDict):
    content_id: str
    content_hash: str
    updated_at: str


def get_hash(content_id: str) -> t.Optional[HashResult]:
    if not content_id:
        return None
    table = dynamodb.Table(DYNAMODB_TABLE)
    record = PipelinePDQHashRecord.get_from_content_id(
        table, f"{IMAGE_FOLDER_KEY}{content_id}"
    )
    if not record:
        return None
    return {
        "content_id": record.content_id[IMAGE_FOLDER_KEY_LEN:],
        "content_hash": record.content_hash,
        "updated_at": record.updated_at.isoformat(),
    }


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
                    signals=[SignalSourceType(type="HASH_PDQ", count=total)],
                    updated_at="TODO",
                )
            )
    return signals


class DashboardCount(t.TypedDict):
    total: int
    today: int
    updated_at: str


class DashboardSystemStatus(t.TypedDict):
    status: str
    days_running: int
    updated_at: str


def get_dashboard_hashes() -> DashboardCount:
    return get_count_from_record_cls(PipelinePDQHashRecord)


def get_dashboard_matches() -> DashboardCount:
    return get_count_from_record_cls(PDQMatchRecord)


def get_count_from_record_cls(record_cls: t.Type[PDQRecordBase]) -> DashboardCount:
    # TODO this is an ~inefficient way to do this but connecting to real counts > mock
    now = datetime.datetime.now()
    day_ago = now - datetime.timedelta(1)
    table = dynamodb.Table(DYNAMODB_TABLE)
    total_count = len(record_cls.get_from_time_range(table))
    today_count = len(record_cls.get_from_time_range(table, day_ago.isoformat()))
    return DashboardCount(
        total=total_count,
        today=today_count,
        updated_at=now.isoformat(),
    )


def get_dashboard_actions() -> DashboardCount:
    return DashboardCount(
        total=3456,
        today=27,
        updated_at="MockData and Timestamp",
    )


def get_dashboard_signals() -> DashboardCount:
    """
    note: SIGNALS COUNT != NUMBER OF UNQUIE HASHES
    """
    return DashboardCount(
        total=sum(get_signal_hash_count().values()),
        today=-1,
        updated_at="TODO",
    )


def get_dashboard_system_status() -> DashboardSystemStatus:
    return DashboardSystemStatus(
        status="Running (Mocked)",
        days_running=42,
        updated_at="MockData and Timestamp",
    )


# TODO this method is expensive some cache or memoization method might be a good idea.
def get_signal_hash_count() -> t.Dict[str, int]:
    s3_config = S3ThreatDataConfig(
        threat_exchange_data_bucket_name=THREAT_EXCHANGE_DATA_BUCKET_NAME,
        threat_exchange_data_folder=THREAT_EXCHANGE_DATA_FOLDER,
        threat_exchange_pdq_file_extension=THREAT_EXCHANGE_PDQ_FILE_EXTENSION,
    )
    pdq_storage = ThreatExchangeS3PDQAdapter(
        config=s3_config, metrics_logger=metrics.names.api_hash_count()
    )
    pdq_data_files = pdq_storage.load_data()

    return {file_name: len(rows) for file_name, rows in pdq_data_files.items()}


app.mount(
    "/matches/",
    get_matches_api(
        dynamodb_table=dynamodb.Table(DYNAMODB_TABLE),
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


if __name__ == "__main__":
    app.run()
