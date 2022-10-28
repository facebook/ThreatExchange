# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
from dataclasses import dataclass
import unittest

from threatexchange.content_type.photo import PhotoContent

from hmalib.common.tests.mapping_common import get_default_signal_type_mapping

from hmalib.common.models.bank import BanksTable
from hmalib.common.models.tests.test_signal_uniqueness import BanksTableTestBase


class BankMemberWithKeyTestCase(BanksTableTestBase, unittest.TestCase):
    def _create_bank(self) -> str:
        table_manager = BanksTable(
            self.get_table(), signal_type_mapping=get_default_signal_type_mapping()
        )

        bank = table_manager.create_bank("TEST_Bank", "Test bank description")
        return bank.bank_id

    def test_add_bank_member_with_key(self):
        with self.fresh_dynamodb():
            table_manager = BanksTable(
                self.get_table(), get_default_signal_type_mapping()
            )

            bank_id = self._create_bank()
            bank_member_id = "fooofofofofoof"

            table_manager.add_bank_member_with_key(
                bank_id=bank_id,
                bank_member_id=bank_member_id,
                content_type=PhotoContent,
                storage_bucket=None,
                storage_key=None,
                raw_content=None,
                notes="",
                is_media_unavailable=True,
            )

            with self.assertRaises(KeyError):
                table_manager.add_bank_member_with_key(
                    bank_id=bank_id,
                    bank_member_id=bank_member_id,
                    content_type=PhotoContent,
                    storage_bucket=None,
                    storage_key=None,
                    raw_content=None,
                    notes="",
                    is_media_unavailable=True,
                )
