# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import os
import pickle
import typing as t

from functools import reduce
from urllib.parse import unquote_plus

import boto3
from threatexchange.signal_type.pdq_index import PDQIndex

from hmalib import metrics
from hmalib.common.logging import get_logger
from hmalib.common.s3_adapters import (
    ThreatExchangeS3PDQAdapter,
    S3ThreatDataConfig,
    HashRowT,
)

logger = get_logger(__name__)
s3_client = boto3.client("s3")

PDQ_DATA_FILE_COLUMNS = ["hash", "id", "timestamp", "tags"]

THREAT_EXCHANGE_DATA_BUCKET_NAME = os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"]
THREAT_EXCHANGE_DATA_FOLDER = os.environ["THREAT_EXCHANGE_DATA_FOLDER"]
THREAT_EXCHANGE_PDQ_FILE_EXTENSION = os.environ["THREAT_EXCHANGE_PDQ_FILE_EXTENSION"]
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
    # TODO: This will attempt to load all pdq files everytime any pdq file is updated
    # so if files are updated for c collaborations it will lead to c^2 files being read
    # this can be optimized by no longer being event based but instead running on
    # a timer if the files have changed.
    for record in event["Records"]:
        inner_record = unwrap_if_sns(record)
        if is_s3_testevent(inner_record):
            continue
        for s3_record in inner_record["Records"]:
            bucket_name = s3_record["s3"]["bucket"]["name"]
            file_path = unquote_plus(s3_record["s3"]["object"]["key"])
            if (
                bucket_name == THREAT_EXCHANGE_DATA_BUCKET_NAME
                and file_path.startswith(THREAT_EXCHANGE_DATA_FOLDER)
                and file_path.endswith(THREAT_EXCHANGE_PDQ_FILE_EXTENSION)
            ):
                return True
    return False


def merge_pdq_files(
    accumulator: t.Dict[str, HashRowT], hash_row: HashRowT
) -> t.Dict[str, HashRowT]:
    hash, meta_data = hash_row
    if hash not in accumulator.keys():
        # Add hash as new row
        accumulator[hash] = hash_row
    else:
        # Add new privacy group to existing row
        accumulator[hash][1]["privacy_groups"].update(meta_data["privacy_groups"])
        # Add new 'tags' for privacy group to existing row
        accumulator[hash][1]["tags"].update(meta_data["tags"])
    return accumulator


def lambda_handler(event, context):
    """
    Listens to SQS events fired when new data files are added to the data
    bucket's data directory. If the updated key matches a set of criteria,
    converts the raw data file into an index and writes to an output S3 bucket.

    As per the default configuration, the bucket must be
    - the hashing data bucket eg.
      dipanjanm-hashing-data20210224213427723700000003
    - the key name must be in the ThreatExchange folder (eg. threat_exchange_data/)
    - the key name must be a pdq file ending in ".pdq.te"

    Which means adding new versions of the datasets will not have an effect. You
    must add the exact pdq.te file.
    """

    if not was_pdq_data_updated(event):
        logger.info("PDQ Data Not Updated, skipping")
        return

    logger.info("PDQ Data Updated, updating pdq hash index")
    metrics_logger = metrics.names.pdq_indexer_lambda

    s3_config = S3ThreatDataConfig(
        threat_exchange_data_bucket_name=THREAT_EXCHANGE_DATA_BUCKET_NAME,
        threat_exchange_data_folder=THREAT_EXCHANGE_DATA_FOLDER,
        threat_exchange_pdq_file_extension=THREAT_EXCHANGE_PDQ_FILE_EXTENSION,
    )

    pdq_data_files = ThreatExchangeS3PDQAdapter(
        config=s3_config, metrics_logger=metrics_logger
    ).load_data()

    with metrics.timer(metrics_logger.merge_datafiles):
        logger.info("Merging PDQ Hash files")
        flat_pdq_data = [
            hash_row for pdq_file in pdq_data_files.values() for hash_row in pdq_file
        ]

        merged_pdq_data = reduce(merge_pdq_files, flat_pdq_data, {}).values()

    with metrics.timer(metrics_logger.build_index):
        logger.info("Creating PDQ Hash Index")
        index = PDQIndex.build(merged_pdq_data)

        logger.info("Putting index in S3")
        index_bytes = pickle.dumps(index)

    with metrics.timer(metrics_logger.upload_index):
        s3_client.put_object(
            Bucket=INDEXES_BUCKET_NAME, Key=PDQ_INDEX_KEY, Body=index_bytes
        )

    logger.info("Index update complete")
    metrics.flush()


# For testing purposes so that this can be run from the command line like:
# $ python3 -m hmalib.lambdas.pdq.pdq_indexer
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
                                "key": THREAT_EXCHANGE_DATA_FOLDER
                                + str(privacy_group_id)
                                + THREAT_EXCHANGE_PDQ_FILE_EXTENSION
                            },
                        }
                    }
                ]
            }
        ]
    }

    lambda_handler(data_updated_event, None)
