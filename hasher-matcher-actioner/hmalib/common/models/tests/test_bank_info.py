# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
from dataclasses import dataclass
import unittest

from hmalib.common.tests.mapping_common import get_default_signal_type_mapping

from hmalib.common.models.bank import BanksTable
from hmalib.common.models.tests.test_signal_uniqueness import BanksTableTestBase


@dataclass
class _BankRandomInfo:
    foo: str
    bar: int
    body: t.Set[int]
    ping: str


class BankInfoTestCase(BanksTableTestBase, unittest.TestCase):
    def _create_bank(self) -> str:
        table_manager = BanksTable(
            self.get_table(), signal_type_mapping=get_default_signal_type_mapping()
        )

        bank = table_manager.create_bank("TEST_Bank", "Test bank description")
        return bank.bank_id

    def test_bank_info_serialization_deserialization(self):
        with self.fresh_dynamodb():
            table_manager = BanksTable(
                self.get_table(), get_default_signal_type_mapping()
            )
            bank_id = self._create_bank()

            bank_info = _BankRandomInfo(
                foo="propah", bar=199, body={1, 2, 3, 4, 5}, ping="pong"
            )
            table_manager.update_bank_info(bank_id, bank_info)

            retrieved = table_manager.get_bank_info(bank_id)
            self.assertEquals(bank_info, retrieved)
