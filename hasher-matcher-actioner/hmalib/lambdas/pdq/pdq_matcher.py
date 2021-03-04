# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import logging
import os
import pickle
import boto3
import datetime

from threatexchange.hashing.pdq_faiss_matcher import PDQFlatHashIndex, PDQMultiHashIndex

from hmalib import metrics

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
sns_client = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")

THRESHOLD = 31
LOCAL_INDEX_FILENAME = "/tmp/hashes.index"

INDEXES_BUCKET_NAME = os.environ["INDEXES_BUCKET_NAME"]
PDQ_INDEX_KEY = os.environ["PDQ_INDEX_KEY"]
OUTPUT_TOPIC_ARN = os.environ["PDQ_MATCHES_TOPIC_ARN"]

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]


def save_match_to_datastore(
    table, content_key, te_id, content_hash, current_datetime, te_hash
):
    item = {
        "PK": "c#{}".format(content_key),
        "SK": "te#{}".format(te_id),
        "ContentHash": content_hash,
        "Timestamp": current_datetime.isoformat(),
        "TEHash": te_hash,
        "GSI1-PK": "te#{}".format(te_id),
        "GSI1-SK": "c#{}".format(content_key),
        "HashType": "pdq",
        "GSI2-PK": "type#pdq",
    }
    table.put_item(Item=item)


def get_index(bucket_name, key):
    """
    Load the given index from the s3 bucket and deserialize it
    """
    # TODO Cache this index for a period of time to reduce S3 calls and bandwidth.
    with metrics.timer(metrics.names.pdq_matcher_lambda.download_index):
        with open(LOCAL_INDEX_FILENAME, "wb") as index_file:
            s3_client.download_fileobj(bucket_name, key, index_file)

    with metrics.timer(metrics.names.pdq_matcher_lambda.parse_index):
        result = pickle.load(open(LOCAL_INDEX_FILENAME, "rb"))

    return result


def lambda_handler(event, context):
    table = dynamodb.Table(DYNAMODB_TABLE)

    hash_index: PDQMultiHashIndex = get_index(INDEXES_BUCKET_NAME, PDQ_INDEX_KEY)
    logger.info("loaded_hash_index")

    for sqs_record in event["Records"]:
        message = json.loads(sqs_record["body"])
        if message.get("Event") == "TestEvent":
            logger.info("Disregarding Test Event")
            continue

        hash_str = message["hash"]
        key = message["key"]
        query = [hash_str]
        current_datetime = datetime.datetime.now()

        with metrics.timer(metrics.names.pdq_matcher_lambda.search_index):
            results = hash_index.search(query, THRESHOLD, return_as_ids=True)

        # Only checking one hash at a time for now
        result = results[0]
        if len(result) > 0:
            message_str = "Matches found for key: {} hash: {}, for IDs: {}".format(
                key, hash_str, result
            )
            logger.info(message_str)
            for te_id in result:
                te_hash = hash_index.hash_at(te_id)
                save_match_to_datastore(
                    table, key, te_id, hash_str, current_datetime, te_hash
                )
            sns_client.publish(
                TopicArn=OUTPUT_TOPIC_ARN,
                Subject="Match found in pdq_matcher lambda",
                Message=message_str,
            )
        else:
            logger.info("No matches found for key: {} hash: {}".format(key, hash_str))

    metrics.flush()
