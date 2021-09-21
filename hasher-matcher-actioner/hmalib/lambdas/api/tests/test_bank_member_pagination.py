# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
import json
import unittest
import uuid
from webtest import (
    TestApp as TApp,
)  # (rename so py.test does not confuse it for a test)

from threatexchange.content_type.photo import PhotoContent

from hmalib.common.models.tests.ddb_test_common import DynamoDBTableTestBase
from hmalib.common.models.bank import BanksTable
from hmalib.banks import bank_operations
from hmalib.lambdas.api.bank import get_bank_api

unique_id = lambda: str(uuid.uuid4())


class BankMemberPaginationTestCase(DynamoDBTableTestBase, unittest.TestCase):
    @classmethod
    def get_table_definition(cls) -> t.Any:
        table_name = "test-banks-table"

        # Regenerate using `aws dynamodb describe-table --table-name <prefix>-HMABanks`
        # TODO: Automate refresh of this using a commandline invocation
        return {
            "AttributeDefinitions": [
                {"AttributeName": "BankNameIndex-BankId", "AttributeType": "S"},
                {"AttributeName": "BankNameIndex-BankName", "AttributeType": "S"},
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            "TableName": table_name,
            "KeySchema": [
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "BankNameIndex",
                    "KeySchema": [
                        {"AttributeName": "BankNameIndex-BankName", "KeyType": "HASH"},
                        {"AttributeName": "BankNameIndex-BankId", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        }

    def _create_200_members(self) -> str:
        """Create a bank, 200 members and return bank_id."""
        table_manager = BanksTable(self.get_table())

        bank = table_manager.create_bank("TEST_BANK", "TEST BANK Description")

        for _ in range(200):
            bank_operations.add_bank_member(
                table_manager,
                bank_id=bank.bank_id,
                content_type=PhotoContent,
                raw_content=None,
                storage_bucket="hma-test-media",
                storage_key="videos/breaking-news.mp4",
                notes="",
            )

        return bank.bank_id

    def test_pagination_produces_correct_number_of_pages(self):
        bank_id = self._create_200_members()
        api = TApp(get_bank_api(self.get_table(), "irrelevant_s3_bucket_for_this_test"))

        running_count = 0
        continuation_token = None

        unique_member_ids = set()

        while True:
            if continuation_token:
                response = json.loads(
                    api.get(
                        f"/get-members/{bank_id}?content_type=photo&continuation_token={continuation_token}"
                    ).body
                )
            else:
                response = json.loads(
                    api.get(f"/get-members/{bank_id}?content_type=photo").body
                )

            running_count += len(response["bank_members"])
            continuation_token = response["continuation_token"]

            unique_member_ids.update(
                map(lambda member: member["bank_member_id"], response["bank_members"])
            )

            if continuation_token == None:
                # Last page should not have any continuation_token
                break

        # Checks for total number of items received. Should work with any page size.
        assert running_count == 200

        # Checks that the number of unique member ids is equal to the expected
        # value (ie. no repeats)
        assert len(unique_member_ids) == 200
