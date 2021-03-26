# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import bottle
import boto3
import json
import base64
from dataclasses import dataclass, asdict
import typing as t
from boto3.dynamodb.conditions import Attr
from apig_wsgi import make_lambda_handler
from bottle import response, error


from hmalib.common import get_logger
from hmalib.models import PDQMatchRecord, PipelinePDQHashRecord

# Set to 10MB for /upload
bottle.BaseRequest.MEMFILE_MAX = 10 * 1024 * 1024

app = bottle.default_app()
apig_wsgi_handler = make_lambda_handler(app)

logger = get_logger(__name__)

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

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


@app.get("/matches")
def matches():
    """
    matches API endpoint:
    returns style { matches: [MatchesResult] }
    """
    results = gen_matches()
    logger.debug(results)
    return {"matches": results}


@app.get("/match/<key>")
def match_details(key=None):
    """
    matche details API endpoint:
    return format: match_details : [MatchDetailsResult]
    """
    results = gen_match_details(key)
    logger.debug(results)
    return {"match_details": results}


@app.get("/hash/<key>")
def hashes(key=None):
    """
    hash details API endpoint:
    return format: HashResult
    """
    results = gen_hash(key)
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


# TODO move to its own library
class MatchesResult(t.TypedDict):
    content_id: str
    signal_id: t.Union[str, int]
    signal_source: str
    updated_at: str
    reactions: str  # TODO


def gen_matches() -> t.List[MatchesResult]:
    table = dynamodb.Table(DYNAMODB_TABLE)
    records = PDQMatchRecord.get_from_time_range(table)
    return [
        {
            "content_id": record.content_id[IMAGE_FOLDER_KEY_LEN:],
            "signal_id": record.signal_id,
            "signal_source": record.signal_source,
            "updated_at": record.updated_at.isoformat(),
            "reactions": "TODO",
        }
        for record in records
    ]


class MatchDetailsResult(t.TypedDict):
    content_id: str
    content_hash: str
    signal_id: t.Union[str, int]
    signal_hash: str
    signal_source: str
    updated_at: str


def gen_match_details(content_id: str) -> t.List[MatchDetailsResult]:
    if not content_id:
        return []
    table = dynamodb.Table(DYNAMODB_TABLE)
    records = PDQMatchRecord.get_from_content_id(
        table, f"{IMAGE_FOLDER_KEY}{content_id}"
    )
    return [
        {
            "content_id": record.content_id[IMAGE_FOLDER_KEY_LEN:],
            "content_hash": record.content_hash,
            "signal_id": record.signal_id,
            "signal_hash": record.signal_hash,
            "signal_source": record.signal_source,
            "updated_at": record.updated_at.isoformat(),
        }
        for record in records
    ]


class HashResult(t.TypedDict):
    content_id: str
    content_hash: str
    updated_at: str


def gen_hash(content_id: str) -> t.Optional[HashResult]:
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
