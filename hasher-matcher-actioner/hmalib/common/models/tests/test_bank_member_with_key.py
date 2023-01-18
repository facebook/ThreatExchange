# Copyright (c) Meta Platforms, Inc. and affiliates.

from contextlib import contextmanager
import typing as t
from dataclasses import dataclass
import unittest

from threatexchange.content_type.photo import PhotoContent
from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal

from hmalib.common.tests.mapping_common import get_default_signal_type_mapping

from hmalib.common.models.bank import BanksTable
from hmalib.common.models.tests.test_signal_uniqueness import BanksTableTestBase


class BankMemberWithKeyTestCase(BanksTableTestBase, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id_count = 0

    def _create_bank(self) -> str:
        """Create a bank with a unique id."""
        self._id_count = self._id_count + 1

        table_manager = BanksTable(
            self.get_table(), signal_type_mapping=get_default_signal_type_mapping()
        )

        bank = table_manager.create_bank(
            f"TEST_Bank_{self._id_count}", "Test bank description"
        )
        return bank.bank_id

    def _add_photo_bank_member_with_key(
        self, table_manager: BanksTable, bank_id: str, member_key: str
    ):
        return table_manager.add_keyed_bank_member(
            bank_id=bank_id,
            member_key=member_key,
            content_type=PhotoContent,
            storage_bucket=None,
            storage_key=None,
            raw_content="does not matter",
            notes="",
            is_media_unavailable=True,
        )

    def test_add_bank_member_with_key(self):
        with self.fresh_table_manager() as table_manager:
            bank_id = self._create_bank()
            member_key = "fooofofofofoof"

            self._add_photo_bank_member_with_key(table_manager, bank_id, member_key)

            with self.assertRaises(KeyError):
                self._add_photo_bank_member_with_key(table_manager, bank_id, member_key)

    def test_add_keyed_bank_member_in_multiple_banks(self):
        with self.fresh_table_manager() as table_manager:
            bank_id = self._create_bank()
            bank_id_2 = self._create_bank()

            member_key = "a-very-unique-id-as-you-can-see"

            bank_member = self._add_photo_bank_member_with_key(
                table_manager, bank_id, member_key
            )

            bank_member_2 = self._add_photo_bank_member_with_key(
                table_manager, bank_id_2, member_key
            )

            self.assertNotEqual(bank_member.bank_member_id, bank_member_2)

    def test_add_multiple_signals_for_keyed_bank_member(self):
        """Prove that multiple signals of the same type can be stored for the
        same bank member. eg. MD5s from slightly altered copies of a video."""
        with self.fresh_table_manager() as table_manager:
            bank_id = self._create_bank()
            member_key = "a-very-unique-id-as-you-can-see"

            PDQ_1 = "f13de9de2e5d46ea51749338e45ea9891a068e17c455bca745ab17de0e7241c4"
            PDQ_2 = "7c455bca745ab17de0e7241c4f13de9de2e5d46ea51749338e45ea9891a068e1"
            MD5 = "7c455bca745ab17de0e7241c4e7241c4"

            bank_member = self._add_photo_bank_member_with_key(
                table_manager, bank_id, member_key
            )

            table_manager.add_bank_member_signal(
                bank_id=bank_id,
                bank_member_id=bank_member.bank_member_id,
                signal_type=PdqSignal,
                signal_value=PDQ_1,
            )
            table_manager.add_bank_member_signal(
                bank_id=bank_id,
                bank_member_id=bank_member.bank_member_id,
                signal_type=PdqSignal,
                signal_value=PDQ_2,
            )
            table_manager.add_bank_member_signal(
                bank_id=bank_id,
                bank_member_id=bank_member.bank_member_id,
                signal_type=VideoMD5Signal,
                signal_value=MD5,
            )

            all_signals = table_manager.get_signals_for_bank_member(
                bank_member.bank_member_id
            )
            self.assertSetEqual(
                {PDQ_1, PDQ_2, MD5},
                {x.signal_value for x in all_signals},
            )
