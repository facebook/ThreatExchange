# Copyright (c) Meta Platforms, Inc. and affiliates.

from contextlib import contextmanager
import unittest
import typing as t
from concurrent import futures

from threatexchange.signal_type.md5 import VideoMD5Signal

from hmalib.common.models.bank import BankedSignalEntry, BanksTable
from hmalib.common.tests.mapping_common import get_default_signal_type_mapping

from .ddb_test_common import DynamoDBTableTestBase


class BanksTableTestBase(DynamoDBTableTestBase):
    @contextmanager
    def fresh_table_manager(self):
        with self.fresh_dynamodb():
            yield BanksTable(
                self.get_table(),
                signal_type_mapping=get_default_signal_type_mapping(),
            )

    @classmethod
    def get_table_definition(cls) -> t.Any:
        table_name = "test-banks-table"

        # Regenerate using `aws dynamodb describe-table --table-name <prefix>-HMABanks`
        # TODO: Automate refresh of this using a commandline invocation
        return {
            "AttributeDefinitions": [
                {
                    "AttributeName": "BankMemberIdIndex-BankMemberId",
                    "AttributeType": "S",
                },
                {
                    "AttributeName": "BankMemberSignalCursorIndex-ChronoKey",
                    "AttributeType": "S",
                },
                {
                    "AttributeName": "BankMemberSignalCursorIndex-SignalType",
                    "AttributeType": "S",
                },
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
                },
                {
                    "IndexName": "BankMemberIdIndex",
                    "KeySchema": [
                        {
                            "AttributeName": "BankMemberIdIndex-BankMemberId",
                            "KeyType": "HASH",
                        }
                    ],
                    "Projection": {"ProjectionType": "KEYS_ONLY"},
                },
                {
                    "IndexName": "BankMemberSignalCursorIndex",
                    "KeySchema": [
                        {
                            "AttributeName": "BankMemberSignalCursorIndex-SignalType",
                            "KeyType": "HASH",
                        },
                        {
                            "AttributeName": "BankMemberSignalCursorIndex-ChronoKey",
                            "KeyType": "RANGE",
                        },
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
        }


class SignalEntryUniquenessTest(BanksTableTestBase, unittest.TestCase):
    # Can generate using `date | md5`
    MD5_VALUE_1 = "e6ecb25a1784f258133e5deac973d700"
    MD5_VALUE_2 = "8f7efbd9e4f1608d41a3a29fe5608829"

    def test_first_write(self):
        entry = BankedSignalEntry.get_unique(
            table=self.get_table(),
            signal_type=VideoMD5Signal,
            signal_value=self.MD5_VALUE_1,
        )
        self.assertIsNotNone(entry)
        self.assertIsNotNone(entry.signal_id)

    def test_subsequent_write(self):
        entry_1 = BankedSignalEntry.get_unique(
            table=self.get_table(),
            signal_type=VideoMD5Signal,
            signal_value=self.MD5_VALUE_1,
        )

        entry_2 = BankedSignalEntry.get_unique(
            table=self.get_table(),
            signal_type=VideoMD5Signal,
            signal_value=self.MD5_VALUE_1,
        )

        self.assertEqual(entry_1.signal_id, entry_2.signal_id)

    def test_stress_writes(self):
        """
        Farms out NUM_WRITES get_unique() calls to a thread pool. Verifies that
        they all have the same signal_id.

        It is hard to assess the validity of this test because moto may be doing
        a single threaded dynamodb implementation. So take this with a pinch of
        salt.
        """
        NUM_WRITES = 500

        md5_value = self.MD5_VALUE_2
        table = self.get_table()
        assertEqual = self.assertEqual

        def get_one_entry() -> str:
            return BankedSignalEntry.get_unique(
                table=table, signal_type=VideoMD5Signal, signal_value=md5_value
            ).signal_id

        with futures.ThreadPoolExecutor(max_workers=4) as pool:
            jobs = [pool.submit(get_one_entry) for _ in range(NUM_WRITES)]

            first_signal_id = None
            for future in futures.as_completed(jobs):
                if first_signal_id is None:
                    first_signal_id = future.result()

                assertEqual(first_signal_id, future.result())
