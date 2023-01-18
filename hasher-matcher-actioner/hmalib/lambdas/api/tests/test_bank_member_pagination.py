# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import json
import unittest
import uuid
from webtest import (
    TestApp as TApp,
)  # (rename so py.test does not confuse it for a test)

from threatexchange.content_type.photo import PhotoContent

from hmalib.common.models.bank import BanksTable
from hmalib.banks import bank_operations
from hmalib.lambdas.api.bank import get_bank_api

from hmalib.common.models.tests.test_signal_uniqueness import BanksTableTestBase
from hmalib.common.tests.mapping_common import get_default_signal_type_mapping

unique_id = lambda: str(uuid.uuid4())


class BankMemberPaginationTestCase(BanksTableTestBase, unittest.TestCase):
    # NOTE: Table is defined in base class BanksTableTestBase

    def _create_200_members(self) -> str:
        """Create a bank, 200 members and return bank_id."""
        table_manager = BanksTable(self.get_table(), get_default_signal_type_mapping())

        bank = table_manager.create_bank("TEST_BANK", "TEST BANK Description")

        for _ in range(200):
            table_manager.add_bank_member(
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
        api = TApp(
            get_bank_api(
                self.get_table(),
                "irrelevant_s3_bucket_for_this_test",
                "irrelevant_sqs_queue",
                get_default_signal_type_mapping(),
            )
        )

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
