# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import logging
import os
import bottle
import boto3
import json
from boto3.dynamodb.conditions import Attr
from apig_wsgi import make_lambda_handler
from bottle import response, error

app = bottle.default_app()
apig_wsgi_handler = make_lambda_handler(app)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
IMAGE_BUCKET_NAME = os.environ["IMAGE_BUCKET_NAME"]
IMAGE_FOLDER_KEY = os.environ["IMAGE_FOLDER_KEY"]

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
    uploaded = bottle.request.files.get("upload")
    # TODO a whole bunch of validation and error checking...
    s3_client.upload_file(
        Fileobj=uploaded.file,
        Bucket=IMAGE_BUCKET_NAME,
        Key=f"{IMAGE_FOLDER_KEY}{uploaded.filename}",
    )

    return {
        "message": "uploaded!",
    }


@app.get("/matches")
def matches():
    results = check_db_for_matches()
    logger.info(results)
    matches = []
    for match in results:
        matches.append({match["PK"]: match["SK"]})
    return {"matches": matches}


@app.get("/hash/<key>")
def hashes(key=None):
    results = check_db_for_hash(key)
    logger.info(results)
    return results


def lambda_handler(event, context):
    """
    root request handler
    """
    logger.info("Received event: " + json.dumps(event, indent=2))
    response = apig_wsgi_handler(event, context)
    logger.info("Response event: " + json.dumps(response, indent=2))
    return response


# TODO move to utils library
def check_db_for_matches():
    table = dynamodb.Table(DYNAMODB_TABLE)
    result = table.scan(
        ProjectionExpression="SK,PK",
        FilterExpression=Attr("SK").begins_with("te#"),
    )
    return result.get("Items")


def check_db_for_hash(key):
    table = dynamodb.Table(DYNAMODB_TABLE)
    result = table.scan(
        ProjectionExpression="ContentHash",
        FilterExpression=(Attr("PK").eq(f"c#images/{key}") & Attr("SK").eq("type#pdq")),
    )
    return result.get("Items")
