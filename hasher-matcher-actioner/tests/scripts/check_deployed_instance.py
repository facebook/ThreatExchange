#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Utility script to confirm the basic functionally of a deployed hma instance
"""

import typing as t
import logging
import os
import boto3
from botocore.exceptions import ClientError
import time
import sys

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# Copy of what is configured in tf files (not worth building a parser for them for single point of mataince imo)
THREAT_EXCHANGE_PDQ_DATA_KEY = "threat_exchange_data/pdq.te"
PDQ_INDEX_KEY = "index/pdq_hashes.index"

# Test uses hasher-matcher-actioner/tests/data/b.jpg
TEST_PHOTO_KEY = "images/test_photo.jpg"
TEST_PHOTO_EXPECTED_HASH = (
    "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22"
)
TEST_PHOTO_EXPECTED_ID = "5555555555555555"

TEST_TE_DATA_PDQ = f"""0000000000000000000000000000000000000000000000000000000000000000,0000000000000001,2020-07-31T18:47:52+0000,tag1 tag2 tag3
000000000000000000000000000000000000000000000000000000000000ffff,0000000000000001,2020-07-31T18:47:52+0000,tag1 tag2 tag3
0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f,0000000000000002,2020-07-31T18:47:52+0000,tag1 tag2 tag3
f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0,0000000000000003,2020-07-31T18:47:52+0000,tag1 tag2 tag3
ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,0000000000000004,2020-07-31T18:47:52+0000,tag1 tag2 tag3
1111111111111111111111111111111111111111111111111111111111111111,0000000000000005,2020-07-31T18:47:52+0000,tag1 tag2 tag3
{TEST_PHOTO_EXPECTED_HASH},{TEST_PHOTO_EXPECTED_ID},2020-07-31T18:47:52+0000,tag1 tag2 tag3
"""


class TestError(Exception):
    """
    Wrapper for exceptions which cause return codes
    """

    def __init__(self, message: str, returncode: int = 1) -> None:
        super().__init__(message)
        self.returncode = returncode


def upload_s3_object(bucket: str, key: str, body: str) -> None:
    """
    Uploads an object, throws if upload fails.
    put_object only returns if succesful and will overwrite anything
    currently in the bucket with this key.
    """
    try:
        print(f"Attempting to upload {key}...")
        s3_client.put_object(Bucket=bucket, Key=key, Body=body)
    except ClientError as e:
        raise TestError(e.msg)


def wait_for_s3_object(bucket: str, key: str, wait_time=5, retries=20) -> None:
    """
    Waits for specfic object in given s3 bucket.
    """
    try:
        print(f"Looking for {key} in {bucket} (check every {wait_time}s x{retries})...")
        waiter = s3_client.get_waiter("object_exists")
        waiter.wait(
            Bucket=bucket,
            Key=key,
            WaiterConfig={"Delay": wait_time, "MaxAttempts": retries},
        )
    except ClientError as e:
        raise TestError(e.msg)


def wait_for_db_item(
    table, key: t.Dict, attributes: t.List, wait_time=5, retries=20
) -> t.Dict:
    """
    Query in a retry loop for a specfic item in table.
    """
    try:
        print(f"Looking for {key} in {table} (check every {wait_time}s x{retries})...")
        while retries > 0:
            result = table.get_item(
                Key=key,
                AttributesToGet=attributes,
            )
            if "Item" in result:
                return result["Item"]
            time.sleep(wait_time)
            retries -= 1
        return {}
    except ClientError as e:
        raise TestError(e.msg)


def run(bucket: str, table) -> bool:
    """
    ~End-to-end test of HMA that:
    uploads TE data -> looks for the index
    uploads a photo -> looks for the hash and a match

    throws TestError if it encoutners unexpected results

    TODO break method into reusable subflows
    """
    # Upload TE Data
    upload_s3_object(bucket, THREAT_EXCHANGE_PDQ_DATA_KEY, TEST_TE_DATA_PDQ)

    # Index created?
    wait_for_s3_object(bucket, PDQ_INDEX_KEY)

    # Upload Photo
    with open(os.path.dirname(__file__) + "/../data/b.jpg", "rb") as data:
        upload_s3_object(bucket, TEST_PHOTO_KEY, data.read())

    # Hash to exist?
    result = wait_for_db_item(
        table,
        key={"PK": f"c#{TEST_PHOTO_KEY}", "SK": "type#pdq"},
        attributes=["ContentHash", "HashType"],
    )
    if "ContentHash" not in result:
        raise TestError("Failed to find hash")
    if result["ContentHash"] != TEST_PHOTO_EXPECTED_HASH:
        raise TestError("Found Incorrect Hash")

    # match found?
    result = wait_for_db_item(
        table,
        key={"PK": f"c#{TEST_PHOTO_KEY}", "SK": f"te#{TEST_PHOTO_EXPECTED_ID}"},
        attributes=["HashType"],
    )
    if "HashType" not in result:
        raise TestError("Failed to find match")


def cleanup(bucket, table):
    """
    Delete all the objects created in run.
    """
    print(
        "Cleaning up...   ",
    )
    table.delete_item(
        Key={"PK": f"c#{TEST_PHOTO_KEY}", "SK": f"te#{TEST_PHOTO_EXPECTED_ID}"},
    )
    table.delete_item(
        Key={"PK": f"c#{TEST_PHOTO_KEY}", "SK": "type#pdq"},
    )
    s3_client.delete_object(Bucket=bucket, Key=TEST_PHOTO_KEY)
    s3_client.delete_object(Bucket=bucket, Key=PDQ_INDEX_KEY)
    s3_client.delete_object(Bucket=bucket, Key=THREAT_EXCHANGE_PDQ_DATA_KEY)
    print("Deleted s3 objects and datastore items")


def main():
    """
    Attempts to run the test, if run throws it will try to clean up before exiting.
    """
    print("\nChecking deployed instance...")
    PREFIX = os.environ["TF_PREFIX"]
    BUCKET_NAME = os.environ["TF_BUCKET_NAME"]
    DYNAMODB_TABLE = os.environ["TF_DYNAMODB_TABLE"]
    table = dynamodb.Table(DYNAMODB_TABLE)
    print(f"Running against instance using prefix: {PREFIX}")
    try:
        run(BUCKET_NAME, table)
    except TestError as e:
        print(e, file=sys.stderr)
        try:
            cleanup(BUCKET_NAME, table)
        finally:
            sys.exit(e.returncode)

    cleanup(BUCKET_NAME, table)
    print("\nSuccess! Deployed instance seems to behave as expected!")
    print(
        'Remember to run "terraform destroy" or "make dev_destroy_instance" if you are done with your deployed instance.'
    )


if __name__ == "__main__":
    main()
