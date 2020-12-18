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
INDEX_S3_KEY = "index/hashes.index"
LOCAL_INDEX_FILENAME = "/tmp/hashes.index"


def get_index(bucket_name, key):
    """
    Load the given index from the s3 bucket and deserialize it
    """
    with open(LOCAL_INDEX_FILENAME, "wb") as index_file:
        s3_client.download_fileobj(bucket_name, key, index_file)
    return pickle.load(open(LOCAL_INDEX_FILENAME, "rb"))


def lambda_handler(event, context):
    logger.info("pdq_matcher_called")
    OUTPUT_TOPIC_ARN = os.environ["PDQ_MATCHES_TOPIC_ARN"]
    DATA_BUCKET = os.environ["DATA_BUCKET"]

    hash_index = get_index(DATA_BUCKET, INDEX_S3_KEY)
    logger.info("loaded_hash_index")
    for sqs_record in event["Records"]:
        sns_notification = json.loads(sqs_record["body"])
        message = json.loads(sns_notification["Message"])
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
