# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Create a bank and fill it with videos for testing.
Replace table_name, test_bank_name, num_members
"""

import os
from hmalib.common.models.models_base import DynamoDBItem
from hmalib.common.models.bank import BanksTable, BankMember
from threatexchange.content_type.video import VideoContent
from mypy_boto3_dynamodb.service_resource import Table
import boto3

dynamodb = boto3.resource("dynamodb")
table_name = ""
test_bank_name = ""
num_members = 1000

# must add thes values
assert table_name != ""
assert test_bank_name != ""

table = dynamodb.Table(table_name)
table_manager = BanksTable(table)

bank = table_manager.create_bank(test_bank_name, "test bank description")

for _ in range(num_members):
    table_manager.add_bank_member(
        bank_id=bank.bank_id,
        content_type=VideoContent,
        raw_content=None,
        storage_bucket="hma-test-media",
        storage_key="videos/breaking-news.mp4",
        notes="",
    )
