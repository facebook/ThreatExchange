# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
import unittest

from threatexchange.content_type.video import VideoContent
from threatexchange.signal_type.video_tmk_pdqf import VideoTmkPdqfSignal

from hmalib.common.models.bank import BanksTable
from hmalib.common.models.tests.test_signal_uniqueness import BanksTableTestBase


class BankMemberRemovesTestCase(BanksTableTestBase, unittest.TestCase):
    # Note: Table is defined in base class BanksTableTestBase

    def _create_bank_and_bank_member(self) -> t.Tuple[str, str]:
        table_manager = BanksTable(self.get_table())

        bank = table_manager.create_bank("TEST_BANK", "Test bank description")
        bank_member = table_manager.add_bank_member(
            bank_id=bank.bank_id,
            content_type=VideoContent,
            raw_content=None,
            storage_bucket="hma-test-media",
            storage_key="irrrelevant",
            notes="",
        )

        return (bank.bank_id, bank_member.bank_member_id)

    def test_bank_member_removes(self):
        with self.fresh_dynamodb():
            table_manager = BanksTable(self.get_table())
            bank_id, bank_member_id = self._create_bank_and_bank_member()

            bank_member_signal_1 = table_manager.add_bank_member_signal(
                bank_id=bank_id,
                bank_member_id=bank_member_id,
                signal_type=VideoTmkPdqfSignal,
                signal_value="A VIDEO TMK PDQF SIGNAL. WILTY?",
            )

            bank_member_signal_2 = table_manager.add_bank_member_signal(
                bank_id=bank_id,
                bank_member_id=bank_member_id,
                signal_type=VideoTmkPdqfSignal,
                signal_value="ANOTHER VIDEO TMK PDQF SIGNAL. WILTY?",
            )

            bank_member_signal_3 = table_manager.add_bank_member_signal(
                bank_id=bank_id,
                bank_member_id=bank_member_id,
                signal_type=VideoTmkPdqfSignal,
                signal_value="An ANOTHER VIDEO TMK PDQF SIGNAL. WILTY?",
            )

            # expect this to now be available to process
            to_process = table_manager.get_bank_member_signals_to_process_page(
                signal_type=VideoTmkPdqfSignal
            )

            self.assertEqual(len(to_process.items), 3)

            table_manager.remove_bank_member_signals_to_process(
                bank_member_id=bank_member_id
            )

            # expect this to now be available to process
            to_process = table_manager.get_bank_member_signals_to_process_page(
                signal_type=VideoTmkPdqfSignal
            )

            self.assertEqual(len(to_process.items), 0)