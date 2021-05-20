# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
from contextlib import contextmanager
from moto import mock_dynamodb2
from hmalib import models
from hmalib.common import signal_models
from hmalib.common.count_models import MatchByPrivacyGroupCounter

import boto3
import datetime
import os


class TestPDQModels(unittest.TestCase):
    table = None
    TEST_CONTENT_ID = "image/test_photo.jpg"
    TEST_SIGNAL_ID = "5555555555555555"
    TEST_SIGNAL_SOURCE = "test_source"
    TEST_DATASET_ID = "sample_data"

    @staticmethod
    def mock_aws_credentials():
        """
        Mocked AWS Credentials for moto.
        (likely not needed based on local testing but just incase)
        """
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"

    @classmethod
    def setUpClass(cls):
        cls.mock_aws_credentials()
        cls.mock_dynamodb2 = mock_dynamodb2()
        cls.mock_dynamodb2.start()
        cls.create_mocked_table()

    @classmethod
    def tearDownClass(cls):
        cls.mock_dynamodb2.stop()

    @classmethod
    def create_mocked_table(cls):
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table_name = "test-table"
        cls.table = dynamodb.create_table(
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1-PK", "AttributeType": "S"},
                {"AttributeName": "GSI1-SK", "AttributeType": "S"},
                {"AttributeName": "GSI2-PK", "AttributeType": "S"},
                {"AttributeName": "UpdatedAt", "AttributeType": "S"},
            ],
            TableName=table_name,
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI-1",
                    "KeySchema": [
                        {"AttributeName": "GSI1-PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1-SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "INCLUDE",
                        "NonKeyAttributes": [
                            "ContentHash",
                            "UpdatedAt",
                            "SignalHash",
                            "SignalSource",
                            "HashType",
                        ],
                    },
                },
                {
                    "IndexName": "GSI-2",
                    "KeySchema": [
                        {"AttributeName": "GSI2-PK", "KeyType": "HASH"},
                        {"AttributeName": "UpdatedAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "INCLUDE",
                        "NonKeyAttributes": [
                            "ContentHash",
                            "SignalHash",
                            "SignalSource",
                            "HashType",
                        ],
                    },
                },
            ],
        )

    @staticmethod
    def get_example_pdq_hash_record():
        return models.PipelinePDQHashRecord(
            TestPDQModels.TEST_CONTENT_ID,
            "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
            datetime.datetime.now(),
            100,
        )

    @staticmethod
    def get_example_pdq_match_record():
        pdq_hash = "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0"
        signal_hash = "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f1"
        return models.PDQMatchRecord(
            TestPDQModels.TEST_CONTENT_ID,
            pdq_hash,
            datetime.datetime.now(),
            TestPDQModels.TEST_SIGNAL_ID,
            TestPDQModels.TEST_SIGNAL_SOURCE,
            signal_hash,
        )

    @staticmethod
    def get_example_pdq_signal_metadata():
        pdq_hash = "a0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0"
        return signal_models.PDQSignalMetadata(
            signal_id=TestPDQModels.TEST_SIGNAL_ID,
            ds_id=TestPDQModels.TEST_DATASET_ID,
            updated_at=datetime.datetime.now(),
            signal_source=TestPDQModels.TEST_SIGNAL_SOURCE,
            signal_hash=pdq_hash,
            tags=["test_tag1", "test_tag2"],
        )

    def test_write_hash_record(self):
        """
        Test PipelinePDQHashRecord write table with hardcode query
        """
        record = self.get_example_pdq_hash_record()

        record.write_to_table(self.table)

        result = self.table.get_item(
            Key={"PK": f"c#{TestPDQModels.TEST_CONTENT_ID}", "SK": "type#pdq"}
        )
        items = result.get("Item")
        content_hash = items.get("ContentHash")
        assert record.content_hash == content_hash

    def test_query_hash_record(self):
        """
        Test PipelinePDQHashRecord write table with get_from_content_key query
        """

        record = self.get_example_pdq_hash_record()
        record.write_to_table(self.table)

        query_record = models.PipelinePDQHashRecord.get_from_content_id(
            self.table, TestPDQModels.TEST_CONTENT_ID
        )

        assert record == query_record

    def test_query_hash_record_by_time(self):
        """
        Test PipelinePDQHashRecord write table with get_from_content_key query by time
        """

        record = self.get_example_pdq_hash_record()

        record.write_to_table(self.table)

        query_record = models.PipelinePDQHashRecord.get_from_time_range(self.table)[0]

        assert record == query_record

    def test_write_match_record(self):
        """
        Test PDQMatchRecord write table with hardcode query
        """

        record = self.get_example_pdq_match_record()

        record.write_to_table(self.table)

        result = self.table.get_item(
            Key={
                "PK": f"c#{TestPDQModels.TEST_CONTENT_ID}",
                "SK": f"s#{TestPDQModels.TEST_SIGNAL_SOURCE}#{TestPDQModels.TEST_SIGNAL_ID}",
            },
        )
        items = result.get("Item")
        query_hash = items.get("SignalHash")
        assert record.signal_hash == query_hash

    def test_query_match_record_by_content_id(self):
        """
        Test PDQMatchRecord write table with get_from_content_key query
        """

        record = self.get_example_pdq_match_record()

        record.write_to_table(self.table)

        query_record = models.PDQMatchRecord.get_from_content_id(
            self.table, TestPDQModels.TEST_CONTENT_ID
        )[0]

        assert record == query_record

    def test_query_match_record_by_signal_id(self):
        """
        Test PDQMatchRecord write table with get_from_content_key query by signal
        """

        record = self.get_example_pdq_match_record()

        record.write_to_table(self.table)

        query_record = models.PDQMatchRecord.get_from_signal(
            self.table, TestPDQModels.TEST_SIGNAL_ID, TestPDQModels.TEST_SIGNAL_SOURCE
        )[0]

        assert record == query_record

    def test_query_match_record_by_time(self):
        """
        Test PDQMatchRecord write table with get_from_content_key query by time
        """

        record = self.get_example_pdq_match_record()

        record.write_to_table(self.table)

        query_record = models.PDQMatchRecord.get_from_time_range(self.table)[0]

        assert record == query_record

    def test_pdq_signal_metadata_manually(self):
        """
        Test PDQSignalMetadata write table
        """
        metadata = self.get_example_pdq_signal_metadata()

        metadata.write_to_table(self.table)

        result = self.table.get_item(
            Key={
                "PK": f"s#{TestPDQModels.TEST_SIGNAL_SOURCE}#{TestPDQModels.TEST_SIGNAL_ID}",
                "SK": f"ds#{TestPDQModels.TEST_DATASET_ID}",
            },
        )
        items = result.get("Item")
        query_hash = items.get("SignalHash")
        assert metadata.signal_hash == query_hash
        for tag in metadata.tags:
            assert tag in items.get("Tags")

    def test_pdq_signal_metadata_by_signal(self):
        """
        Test PDQSignalMetadata write table with get_from_signal
        """
        metadata = self.get_example_pdq_signal_metadata()

        metadata.write_to_table(self.table)

        query_metadata = signal_models.PDQSignalMetadata.get_from_signal(
            self.table, TestPDQModels.TEST_SIGNAL_ID, TestPDQModels.TEST_SIGNAL_SOURCE
        )[0]

        assert metadata.signal_hash == query_metadata.signal_hash
        for tag in metadata.tags:
            assert tag in query_metadata.tags

    def test_pdq_signal_metadata_update_tags_in_table(self):
        """
        Test PDQSignalMetadata write to table with update_tags_in_table_if_exists
        """
        metadata = self.get_example_pdq_signal_metadata()

        # change id since table persists betweeen test
        new_signal_id = "123456789"
        metadata.signal_id = new_signal_id

        # first attempt at update should return false (doesn't exist)
        assert not metadata.update_tags_in_table_if_exists(self.table)

        metadata.write_to_table(self.table)

        query_metadata = signal_models.PDQSignalMetadata.get_from_signal(
            self.table, new_signal_id, TestPDQModels.TEST_SIGNAL_SOURCE
        )[0]
        assert metadata.signal_hash == query_metadata.signal_hash
        for tag in metadata.tags:
            assert tag in query_metadata.tags

        replaced_tags = ["new", "list", "of", "tags"]
        metadata.tags = replaced_tags

        # second attmept at update should succeed
        assert metadata.update_tags_in_table_if_exists(self.table)
        query_metadata = signal_models.PDQSignalMetadata.get_from_signal(
            self.table, new_signal_id, TestPDQModels.TEST_SIGNAL_SOURCE
        )[0]
        for tag in replaced_tags:
            assert tag in query_metadata.tags

    def test_pdq_signal_metadata_update_pending_chage_in_table(self):
        """
        Test PDQSignalMetadata write to table with update_pending_opinion_change_in_table_if_exists
        """
        metadata = self.get_example_pdq_signal_metadata()

        # change id since table persists betweeen test
        new_signal_id = "987654321"
        metadata.signal_id = new_signal_id

        # first attempt at update should return false (doesn't exist)
        assert not metadata.update_pending_opinion_change_in_table_if_exists(self.table)

        metadata.write_to_table(self.table)

        query_metadata = signal_models.PDQSignalMetadata.get_from_signal(
            self.table, new_signal_id, TestPDQModels.TEST_SIGNAL_SOURCE
        )[0]
        assert metadata.signal_hash == query_metadata.signal_hash
        assert (
            signal_models.PendingOpinionChange.NONE.value
            == query_metadata.pending_opinion_change.value
        )

        metadata.pending_opinion_change = (
            signal_models.PendingOpinionChange.MARK_TRUE_POSITIVE
        )

        # second attmept at update should succeed
        assert metadata.update_pending_opinion_change_in_table_if_exists(self.table)
        query_metadata = signal_models.PDQSignalMetadata.get_from_signal(
            self.table, new_signal_id, TestPDQModels.TEST_SIGNAL_SOURCE
        )[0]
        assert (
            signal_models.PendingOpinionChange.MARK_TRUE_POSITIVE.value
            == query_metadata.pending_opinion_change.value
        )


class CountersTest(TestPDQModels):
    @contextmanager
    def fresh_dynamodb(self):
        # Code to acquire resource, e.g.:
        self.__class__.setUpClass()
        try:
            yield
        finally:
            self.__class__.tearDownClass()

    def test_writes_init_counters(self):
        """
        Test that the first write creates a counter.
        """
        with self.fresh_dynamodb():
            record = self.get_example_pdq_hash_record()
            record.write_to_table(self.table)

            assert 1 == models.PipelinePDQHashRecord.get_total_count(self.table)

    def test_writes_inc_counters(self):
        """
        Test that subsequent writes increment counters.
        """
        with self.fresh_dynamodb():
            record = self.get_example_pdq_hash_record()
            record.write_to_table(self.table)
            record.write_to_table(self.table)
            record.write_to_table(self.table)
            record.write_to_table(self.table)

            assert 4 == models.PipelinePDQHashRecord.get_total_count(self.table)

    def test_writes_inc_counters_only_for_the_updated_class(self):
        """
        Test that the writes do not increment counters for other classes.
        """
        with self.fresh_dynamodb():
            record = self.get_example_pdq_hash_record()
            record.write_to_table(self.table)
            record.write_to_table(self.table)
            record.write_to_table(self.table)
            record.write_to_table(self.table)

            assert 0 == models.PDQMatchRecord.get_total_count(self.table)


class MatchByPrivacyGroupCounterTestCase(CountersTest):
    """
    Better placed inside common, but unfortunately has to be here.

    To be able to re-use the ddb schema definitions, must place things here.
    tests are module free so can't be cross-referenced.
    """

    def test_full_flow(self):
        with self.fresh_dynamodb():
            # Before anything has been done.
            self.assertEqual({}, MatchByPrivacyGroupCounter.get_all_counts(self.table))
            self.assertEqual(
                0, MatchByPrivacyGroupCounter.get_count(self.table, "specific-pg")
            )

            # Do an update
            MatchByPrivacyGroupCounter.increment_counts(
                self.table, {"a-privacy-group": 100, "another-privacy-group": 32}
            )

            self.assertEqual(
                {"a-privacy-group": 100, "another-privacy-group": 32},
                MatchByPrivacyGroupCounter.get_all_counts(self.table),
            )

            # Do another update
            MatchByPrivacyGroupCounter.increment_counts(
                self.table, {"a-privacy-group": 100, "another-privacy-group": 32}
            )

            self.assertEqual(
                {"a-privacy-group": 200, "another-privacy-group": 64},
                MatchByPrivacyGroupCounter.get_all_counts(self.table),
            )

            self.assertEqual(
                200, MatchByPrivacyGroupCounter.get_count(self.table, "a-privacy-group")
            )
