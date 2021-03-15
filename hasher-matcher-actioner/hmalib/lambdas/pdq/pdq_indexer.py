# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import codecs
import csv
import json
import os
import pickle
from urllib.parse import unquote_plus

import boto3
from threatexchange.signal_type.pdq_index import PDQIndex

from hmalib import metrics
from hmalib.common import get_logger

logger = get_logger(__name__)
s3_client = boto3.client("s3")

PDQ_DATA_FILE_COLUMNS = ["hash", "id", "timestamp", "tags"]

THREAT_EXCHANGE_DATA_BUCKET_NAME = os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"]
THREAT_EXCHANGE_PDQ_DATA_KEY = os.environ["THREAT_EXCHANGE_PDQ_DATA_KEY"]

INDEXES_BUCKET_NAME = os.environ["INDEXES_BUCKET_NAME"]
PDQ_INDEX_KEY = os.environ["PDQ_INDEX_KEY"]


def unwrap_if_sns(data):
    if "EventSource" in data and data["EventSource"] == "aws:sns":
        message = data["Sns"]["Message"]
        return json.loads(message)
    return data


def is_s3_testevent(data):
    return "Event" in data and data["Event"] == "s3:TestEvent"


def was_pdq_data_updated(event):
    for record in event["Records"]:
        inner_record = unwrap_if_sns(record)
        if is_s3_testevent(inner_record):
            continue
        for s3_record in inner_record["Records"]:
            bucket_name = s3_record["s3"]["bucket"]["name"]
            key = unquote_plus(s3_record["s3"]["object"]["key"])
            if (
                bucket_name == THREAT_EXCHANGE_DATA_BUCKET_NAME
                and key == THREAT_EXCHANGE_PDQ_DATA_KEY
            ):
                return True
    return False


def lambda_handler(event, context):
    """
    Listens to SQS events fired when new data files are added to the data
    bucket's data directory. If the updated key matches a set of criteria,
    converts the raw data file into an index and writes to an output S3 bucket.

    As per the default configuration, the bucket must be
    - the hashing data bucket eg.
      dipanjanm-hashing-data20210224213427723700000003
    - the key name must be threat_exchange_data/pdq.te

    Which means adding new versions of the datasets will not have an effect. You
    must add the exact pdq.te file.
    """

    if not was_pdq_data_updated(event):
        logger.info("PDQ Data Not Updated, skipping")
        return

    logger.info("PDQ Data Updated, updating pdq hash index")

    logger.info("Retreiving PDQ Data from S3")

    with metrics.timer(metrics.names.pdq_indexer_lambda.download_datafile):
        pdq_data_file = s3_client.get_object(
            Bucket=THREAT_EXCHANGE_DATA_BUCKET_NAME, Key=THREAT_EXCHANGE_PDQ_DATA_KEY
        )

    with metrics.timer(metrics.names.pdq_indexer_lambda.parse_datafile):
        pdq_data_reader = csv.DictReader(
            codecs.getreader("utf-8")(pdq_data_file["Body"]),
            fieldnames=PDQ_DATA_FILE_COLUMNS,
        )
        pdq_data = [
            (
                row["hash"],
                # Also add hash to metadata for easy look up on match
                {
                    "id": int(row["id"]),
                    "hash": row["hash"],
                },
            )
            for row in pdq_data_reader
        ]

    with metrics.timer(metrics.names.pdq_indexer_lambda.build_index):
        logger.info("Creating PDQ Hash Index")

        index = PDQIndex.build(pdq_data)

        logger.info("Putting index in S3")
        index_bytes = pickle.dumps(index)

    with metrics.timer(metrics.names.pdq_indexer_lambda.upload_index):
        s3_client.put_object(
            Bucket=INDEXES_BUCKET_NAME, Key=PDQ_INDEX_KEY, Body=index_bytes
        )

    logger.info("Index update complete")
    metrics.flush()
