# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import logging
import os
import pickle
import boto3

from threatexchange.hashing.pdq_faiss_matcher import PDQFlatHashIndex, PDQMultiHashIndex

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
sns_client = boto3.client("sns")

THRESHOLD = 31
LOCAL_INDEX_FILENAME = "/tmp/hashes.index"

INDEXES_BUCKET_NAME = os.environ["INDEXES_BUCKET_NAME"]
PDQ_INDEX_KEY = os.environ["PDQ_INDEX_KEY"]
OUTPUT_TOPIC_ARN = os.environ["PDQ_MATCHES_TOPIC_ARN"]


def get_index(bucket_name, key):
    """
    Load the given index from the s3 bucket and deserialize it
    """
    with open(LOCAL_INDEX_FILENAME, "wb") as index_file:
        s3_client.download_fileobj(bucket_name, key, index_file)
    return pickle.load(open(LOCAL_INDEX_FILENAME, "rb"))


def lambda_handler(event, context):
    logger.info("pdq_matcher_called")

    hash_index = get_index(INDEXES_BUCKET_NAME, PDQ_INDEX_KEY)
    logger.info("loaded_hash_index")
    for sqs_record in event["Records"]:
        message = json.loads(sqs_record["body"])
        if message.get("Event") == "TestEvent":
            logger.info("Disregarding Test Event")
            continue
        hash_str = message["hash"]
        key = message["key"]
        query = [hash_str]
        results = hash_index.search(query, THRESHOLD, return_as_ids=True)
        # Only checking one hash at a time for now
        result = results[0]
        if len(result) > 0:
            message_str = "Matches found for key: {} hash: {}, for IDs: {}".format(
                key, hash_str, result
            )
            logger.info(message_str)
            sns_client.publish(
                TopicArn=OUTPUT_TOPIC_ARN,
                Subject="Match found in pdq_matcher lambda",
                Message=message_str,
            )
        else:
            logger.info("No matches found for key: {} hash: {}".format(key, hash_str))
