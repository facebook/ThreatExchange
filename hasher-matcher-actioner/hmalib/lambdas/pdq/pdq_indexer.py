# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import codecs
import csv
import json
import os
import pickle
import typing as t

from functools import reduce
from urllib.parse import unquote_plus

import boto3
from threatexchange.signal_type.pdq_index import PDQIndex

from hmalib import metrics
from hmalib.common import get_logger

logger = get_logger(__name__)
s3_client = boto3.client("s3")

PDQ_DATA_FILE_COLUMNS = ["hash", "id", "timestamp", "tags"]

THREAT_EXCHANGE_DATA_BUCKET_NAME = os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"]
THREAT_EXCHANGE_STATE_KEY_PREFIX = os.environ["THREAT_EXCHANGE_STATE_KEY_PREFIX"]
THREAT_EXCHANGE_PDQ_KEY_SUFFIX = os.environ["THREAT_EXCHANGE_PDQ_KEY_SUFFIX"]
INDEXES_BUCKET_NAME = os.environ["INDEXES_BUCKET_NAME"]
PDQ_INDEX_KEY = os.environ["PDQ_INDEX_KEY"]

HashRowType = t.Tuple[str, t.Dict[str, t.Any]]
S3FileType = t.Dict[str, t.Any]


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
                and key.startswith(THREAT_EXCHANGE_STATE_KEY_PREFIX)
                and key.endswith(THREAT_EXCHANGE_PDQ_KEY_SUFFIX)
            ):
                return True
    return False


def get_pdq_file(file_name: str) -> t.Dict[str, S3FileType]:
    return {
        'pdq_file_name' : file_name,
        'pdq_data_file' : s3_client.get_object(Bucket=THREAT_EXCHANGE_DATA_BUCKET_NAME, Key=file_name),
    }


def parse_pdq_file(
    pdq_file_name: str, pdq_data_file: S3FileType
) -> t.List[HashRowType]:
    pdq_data_reader = csv.DictReader(
        codecs.getreader("utf-8")(pdq_data_file["Body"]),
        fieldnames=PDQ_DATA_FILE_COLUMNS,
    )
    return [
        (
            row["hash"],
            # Also add hash to metadata for easy look up on match
            {
                "id": int(row["id"]),
                "hash": row["hash"],
                "source": "te",  # default for now to make downstream easier to generalize
                "privacy_groups": [pdq_file_name.split("/")[-1].split(".")[0]],
            },
        )
        for row in pdq_data_reader
    ]


def merge_pdq_files(
    accumulator: t.Dict[str, HashRowType], hash_row: t.Tuple[str, HashRowType]
) -> t.Dict[str, HashRowType]:
    hash, meta_data = hash_row
    if hash not in accumulator.keys():
        # Add hash as new row
        accumulator[hash] = meta_data
    else:
        # Add new privacy group to existing row
        accumulator[hash]["privacy_groups"].append(meta_data["privacy_groups"][0])
    return accumulator


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

    with metrics.timer(metrics.names.pdq_indexer_lambda.download_datafiles):
        s3_bucket_files = s3_client.list_objects(
            Bucket=THREAT_EXCHANGE_DATA_BUCKET_NAME,
            Prefix=THREAT_EXCHANGE_STATE_KEY_PREFIX,
        )['Contents']
        logger.info("Found " + str(len(s3_bucket_files)) + " Files")

        pdq_data_files = [
            get_pdq_file(file['Key'])
            for file in s3_bucket_files
            if file['Key'].endswith(THREAT_EXCHANGE_PDQ_KEY_SUFFIX)
        ]
        logger.info("Found " + str(len(pdq_data_files)) + " PDQ Files")


    with metrics.timer(metrics.names.pdq_indexer_lambda.parse_datafiles):
        logger.info("Parsing PDQ Hash files")
        pdq_data = [parse_pdq_file(**pdq_data_file) for pdq_data_file in pdq_data_files]


    with metrics.timer(metrics.names.pdq_indexer_lambda.merge_datafiles):
        logger.info("Merging PDQ Hash files")
        flat_pdq_data = [hash_row for pdq_file in pdq_data for hash_row in pdq_file]

        #TODO Currently list of HashRowTypes may need to change
        merged_pdq_data = reduce(merge_pdq_files, flat_pdq_data, {}).items()

    with metrics.timer(metrics.names.pdq_indexer_lambda.build_index):
        logger.info("Creating PDQ Hash Index")
        #TODO This takes an interable Tuple of hash to HashRowTypes
        index = PDQIndex.build(merged_pdq_data)

        logger.info("Putting index in S3")
        index_bytes = pickle.dumps(index)

    with metrics.timer(metrics.names.pdq_indexer_lambda.upload_index):
        s3_client.put_object(
            Bucket=INDEXES_BUCKET_NAME, Key=PDQ_INDEX_KEY, Body=index_bytes
        )

    logger.info("Index update complete")
    metrics.flush()


if __name__ == "__main__":
    privacy_group_id = 1234567890
    data_updated_event = {
        "Records": [
            {
                "Records": [
                    {
                        "s3": {
                            "bucket": {"name": THREAT_EXCHANGE_DATA_BUCKET_NAME},
                            "object": {
                                "key": THREAT_EXCHANGE_STATE_KEY_PREFIX
                                + str(privacy_group_id)
                                + THREAT_EXCHANGE_PDQ_KEY_SUFFIX
                            },
                        }
                    }
                ]
            }
        ]
    }

    lambda_handler(data_updated_event, None)
