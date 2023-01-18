# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import unittest

from hmalib.common.models.count import AggregateCount, CountBuffer, ParameterizedCount
from .ddb_test_common import DynamoDBTableTestBase


class CountsTestBase(DynamoDBTableTestBase):
    @classmethod
    def get_table_definition(cls) -> t.Any:
        table_name = "test-counts-table"

        # Regenerate using `aws dynamodb describe-table --table-name <prefix>-HMACounts`
        return {
            "AttributeDefinitions": [
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            "TableName": table_name,
            "KeySchema": [
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
        }


class CountBuffersTest(CountsTestBase, unittest.TestCase):
    def test_no_writes_until_flush(self):
        """Verify that nothing is written to ddb until the buffer is flushed"""
        buffer = CountBuffer(self.get_table())
        dummy_count_name = "hmatest.something.that.you.measure"

        for i in range(100):
            buffer.inc_aggregate(f"{dummy_count_name}.{i}")

        self.assertEqual(
            AggregateCount(f"{dummy_count_name}.{0}").get_value(self.get_table()), 0
        )

        buffer.flush()

        self.assertEqual(
            AggregateCount(f"{dummy_count_name}.{0}").get_value(self.get_table()),
            1,
        )

    def test_parameterized_writes(self):
        """Verify that parameterized writes are working."""
        buffer = CountBuffer(self.get_table())
        dummy_count_name = "hmatest.something.that.has.parameters"

        for i in range(100):
            buffer.inc_parameterized(dummy_count_name, "paramname", f"paramvalue-{i}")

        buffer.flush()

        # Only verify the last entry.
        self.assertEqual(
            ParameterizedCount(
                dummy_count_name, "paramname", f"paramvalue-{99}"
            ).get_value(self.get_table()),
            1,
        )

    def test_parameterized_get_all(self):
        """Verify that parameterized writes can actually be retrieved."""
        buffer = CountBuffer(self.get_table())
        dummy_count_name = "hmatest.something.else.that.has.parameters"

        for i in range(20):
            buffer.inc_parameterized(dummy_count_name, "paramname", f"paramvalue-{i}")
        buffer.flush()

        counts = ParameterizedCount.get_all(
            dummy_count_name, "paramname", self.get_table()
        )
        self.assertEqual(len(counts), 20)
        self.assertEqual(counts[0].value, "paramvalue-0")
        self.assertEqual(
            counts[-1].value, "paramvalue-9"
        )  # lexically, paramvalue-9 > paramvalue-19
