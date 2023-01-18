# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import unittest

from threatexchange.content_type.video import VideoContent
from threatexchange.signal_type.md5 import VideoMD5Signal

from hmalib.common.models.bank import BanksTable
from hmalib.common.models.tests.test_signal_uniqueness import BanksTableTestBase

from hmalib.common.tests.mapping_common import get_default_signal_type_mapping


class BankMemberRemovesTestCase(BanksTableTestBase, unittest.TestCase):
    # Note: Table is defined in base class BanksTableTestBase

    def _create_bank_and_bank_member(self) -> t.Tuple[str, str]:
        table_manager = BanksTable(
            self.get_table(), signal_type_mapping=get_default_signal_type_mapping()
        )

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
            table_manager = BanksTable(
                self.get_table(), get_default_signal_type_mapping()
            )
            bank_id, bank_member_id = self._create_bank_and_bank_member()

            bank_member_signal_1 = table_manager.add_bank_member_signal(
                bank_id=bank_id,
                bank_member_id=bank_member_id,
                signal_type=VideoMD5Signal,
                signal_value="A VIDEO TMK PDQF SIGNAL. WILTY?",
            )

            bank_member_signal_2 = table_manager.add_bank_member_signal(
                bank_id=bank_id,
                bank_member_id=bank_member_id,
                signal_type=VideoMD5Signal,
                signal_value="ANOTHER VIDEO TMK PDQF SIGNAL. WILTY?",
            )

            bank_member_signal_3 = table_manager.add_bank_member_signal(
                bank_id=bank_id,
                bank_member_id=bank_member_id,
                signal_type=VideoMD5Signal,
                signal_value="An ANOTHER VIDEO TMK PDQF SIGNAL. WILTY?",
            )

            # expect this to now be available to process
            to_process = table_manager.get_bank_member_signals_to_process_page(
                signal_type=VideoMD5Signal
            )

            self.assertEqual(len(to_process.items), 3)

            table_manager.remove_bank_member_signals_to_process(
                bank_member_id=bank_member_id
            )

            # expect this to now be available to process
            to_process = table_manager.get_bank_member_signals_to_process_page(
                signal_type=VideoMD5Signal
            )

            self.assertEqual(len(to_process.items), 0)

    def test_bank_member_removes_from_get_members_page(self):
        NUM_MEMBERS = 100
        REMOVE_EVERY_XTH_MEMBER = 4

        with self.fresh_dynamodb():
            table_manager = BanksTable(
                self.get_table(), get_default_signal_type_mapping()
            )
            bank_id, bank_member_id = self._create_bank_and_bank_member()
            for i in range(NUM_MEMBERS):
                bank_member = table_manager.add_bank_member(
                    bank_id=bank_id,
                    content_type=VideoContent,
                    raw_content=None,
                    storage_bucket="hma-test-media",
                    storage_key="irrrelevant",
                    notes="",
                )

            members = []
            exclusive_start_key = None

            while True:
                page = table_manager.get_all_bank_members_page(
                    bank_id=bank_id,
                    content_type=VideoContent,
                    exclusive_start_key=exclusive_start_key,
                )
                members += page.items
                exclusive_start_key = page.last_evaluated_key

                if not page.has_next_page():
                    break

            self.assertEqual(
                len(members),
                101,
                "All the pages together have as many members as we added.",
            )

            count_members_removed = 0
            for i, member in enumerate(members):
                if i // REMOVE_EVERY_XTH_MEMBER == 0:
                    table_manager.remove_bank_member(member.bank_member_id)
                    count_members_removed += 1

            members = []
            exclusive_start_key = None

            while True:
                page = table_manager.get_all_bank_members_page(
                    bank_id=bank_id,
                    content_type=VideoContent,
                    exclusive_start_key=exclusive_start_key,
                )
                members += page.items
                exclusive_start_key = page.last_evaluated_key

                if not page.has_next_page():
                    break

            self.assertEqual(
                len(members),
                101 - count_members_removed,
                "All the pages together have as many members as we added minus the ones we removed.",
            )
