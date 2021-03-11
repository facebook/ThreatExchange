# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import logging
import os
import bottle
import boto3
import json
from boto3.dynamodb.conditions import Attr
from apig_wsgi import make_lambda_handler

app = bottle.default_app()
apig_wsgi_handler = make_lambda_handler(app)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]


@app.get("/echo/<val>")
def echo(val):
    return val


@app.get("/")
def root():
    return {
        "reply": "Hello World, HMA",
    }


@app.get("/matches")
def matches():
    results = check_db_for_matches()
    logger.info(results)
    matches = []
    for match in results:
        matches.append({match["PK"]: match["SK"]})
    return json.dumps({"matches": matches})


@app.get("/hash/<key>")
def hashes(key=None):
    results = check_db_for_hash(key)
    logger.info(results)
    return json.dumps(results)


def lambda_handler(event, context):
    """
    Status of delpoyed HMA
    """
    logger.info("Received event: " + json.dumps(event, indent=2))
    response = apig_wsgi_handler(event, context)
    logger.info("Response event: " + json.dumps(response, indent=2))
    return response


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
