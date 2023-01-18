# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import unittest
import random

from threatexchange.content_type.video import VideoContent
from threatexchange.interface_validation import SignalTypeMapping
from threatexchange.signal_type.md5 import VideoMD5Signal

from hmalib.common.config import HMAConfig
from hmalib.banks import bank_operations
from hmalib.common.models.bank import BanksTable

from hmalib.common.models.tests.test_signal_uniqueness import BanksTableTestBase
from hmalib.common.tests.mapping_common import get_default_signal_type_mapping


class BankMemberSignalsToProcessTestCase(BanksTableTestBase, unittest.TestCase):
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

    def test_single_signal_is_retrieved(self):
        with self.fresh_dynamodb():
            table_manager = BanksTable(
                self.get_table(), get_default_signal_type_mapping()
            )
            bank_id, bank_member_id = self._create_bank_and_bank_member()

            bank_member_signal = table_manager.add_bank_member_signal(
                bank_id=bank_id,
                bank_member_id=bank_member_id,
                signal_type=VideoMD5Signal,
                signal_value="A VIDEO MD5 SIGNAL. WILTY?",
            )

            # expect this to now be available to process
            to_process = table_manager.get_bank_member_signals_to_process_page(
                signal_type=VideoMD5Signal
            )

            self.assertEqual(len(to_process.items), 1)
            self.assertEqual(
                bank_member_signal.signal_id, to_process.items[0].signal_id
            )

    def test_multiple_signals_are_retrieved(self):
        with self.fresh_dynamodb():
            table_manager = BanksTable(
                self.get_table(), get_default_signal_type_mapping()
            )
            bank_id, bank_member_id = self._create_bank_and_bank_member()

            signal_ids = [
                table_manager.add_bank_member_signal(
                    bank_id=bank_id,
                    bank_member_id=bank_member_id,
                    signal_type=VideoMD5Signal,
                    signal_value="A VIDEO MD5 SIGNAL. WILTY?" + str(random.random()),
                ).signal_id
                for _ in range(20)
            ]

            to_process_signal_ids = [
                signal.signal_id
                for signal in table_manager.get_bank_member_signals_to_process_page(
                    signal_type=VideoMD5Signal
                ).items
            ]

            self.assertListEqual(signal_ids, to_process_signal_ids)

    def test_order_of_signals_is_chronological(self):
        with self.fresh_dynamodb():
            table_manager = BanksTable(
                self.get_table(), get_default_signal_type_mapping()
            )
            bank_id, bank_member_id = self._create_bank_and_bank_member()

            signals = [
                table_manager.add_bank_member_signal(
                    bank_id=bank_id,
                    bank_member_id=bank_member_id,
                    signal_type=VideoMD5Signal,
                    signal_value="A VIDEO MD5 SIGNAL. WILTY?" + str(random.random()),
                )
                for _ in range(20)
            ]

            signal_ids_in_order = list(
                map(lambda s: s.signal_id, sorted(signals, key=lambda x: x.updated_at))
            )

            to_process_signal_ids = [
                signal.signal_id
                for signal in table_manager.get_bank_member_signals_to_process_page(
                    signal_type=VideoMD5Signal
                ).items
            ]

            self.assertListEqual(signal_ids_in_order, to_process_signal_ids)

    def test_order_of_signals_multi_page(self):
        with self.fresh_dynamodb():
            table_manager = BanksTable(
                self.get_table(), get_default_signal_type_mapping()
            )
            bank_id, bank_member_id = self._create_bank_and_bank_member()

            signals = [
                table_manager.add_bank_member_signal(
                    bank_id=bank_id,
                    bank_member_id=bank_member_id,
                    signal_type=VideoMD5Signal,
                    signal_value="A VIDEO TMK PDQF SIGNAL. WILTY?"
                    + str(random.random()),
                )
                for _ in range(20)
            ]

            signal_ids_in_order = list(
                map(lambda s: s.signal_id, sorted(signals, key=lambda x: x.updated_at))
            )

            queried_signal_ids = []
            exclusive_start_key = None
            while True:
                response = table_manager.get_bank_member_signals_to_process_page(
                    signal_type=VideoMD5Signal,
                    limit=4,
                    exclusive_start_key=exclusive_start_key,
                )

                exclusive_start_key = response.last_evaluated_key
                queried_signal_ids += [signal.signal_id for signal in response.items]

                if not response.has_next_page():
                    break

            self.assertListEqual(signal_ids_in_order, queried_signal_ids)
