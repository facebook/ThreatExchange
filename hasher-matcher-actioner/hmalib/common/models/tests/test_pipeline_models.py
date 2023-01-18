# Copyright (c) Meta Platforms, Inc. and affiliates.

from decimal import Decimal
import unittest
import datetime

from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal

from hmalib.common.models import pipeline as models
from hmalib.common.models.signal import (
    ThreatExchangeSignalMetadata,
    PendingThreatExchangeOpinionChange,
)

from hmalib.common.tests.mapping_common import get_default_signal_type_mapping
from .ddb_test_common import DynamoDBTableTestBase

# These should change in tandem with terraform/datastore/main.tf
DATASTORE_TABLE_DEF = {
    "AttributeDefinitions": [
        {"AttributeName": "PK", "AttributeType": "S"},
        {"AttributeName": "SK", "AttributeType": "S"},
        {"AttributeName": "GSI1-PK", "AttributeType": "S"},
        {"AttributeName": "GSI1-SK", "AttributeType": "S"},
        {"AttributeName": "GSI2-PK", "AttributeType": "S"},
        {"AttributeName": "UpdatedAt", "AttributeType": "S"},
    ],
    "TableName": "test_table",
    "BillingMode": "PAY_PER_REQUEST",
    "KeySchema": [
        {"AttributeName": "PK", "KeyType": "HASH"},
        {"AttributeName": "SK", "KeyType": "RANGE"},
    ],
    "GlobalSecondaryIndexes": [
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
                    "SignalType",
                    "MatchDistance",
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
                    "SignalType",
                    "MatchDistance",
                ],
            },
        },
    ],
}


class TestPDQModels(DynamoDBTableTestBase, unittest.TestCase):
    TEST_CONTENT_ID = "image/test_photo.jpg"
    TEST_SIGNAL_ID = "5555555555555555"
    TEST_SIGNAL_SOURCE = "test_source"
    TEST_DATASET_ID = "sample_data"

    @classmethod
    def get_table_definition(cls):
        return DATASTORE_TABLE_DEF

    @staticmethod
    def get_example_pdq_hash_record():
        return models.PipelineHashRecord(
            TestPDQModels.TEST_CONTENT_ID,
            PdqSignal,
            "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
            datetime.datetime.now(),
            {"Quality": Decimal("100")},
        )

    @staticmethod
    def get_example_md5_hash_record():
        # Use this somewhere
        return models.PipelineHashRecord(
            TestPDQModels.TEST_CONTENT_ID,
            VideoMD5Signal,
            "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
            datetime.datetime.now(),
        )

    @staticmethod
    def get_example_pdq_match_record():
        pdq_hash = "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0"
        signal_hash = "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f1"

        return models.MatchRecord(
            TestPDQModels.TEST_CONTENT_ID,
            PdqSignal,
            pdq_hash,
            datetime.datetime.now(),
            TestPDQModels.TEST_SIGNAL_ID,
            TestPDQModels.TEST_SIGNAL_SOURCE,
            signal_hash,
        )

    @staticmethod
    def get_example_pdq_signal_metadata():
        pdq_hash = "a0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0"
        return ThreatExchangeSignalMetadata(
            signal_id=TestPDQModels.TEST_SIGNAL_ID,
            privacy_group_id=TestPDQModels.TEST_DATASET_ID,
            updated_at=datetime.datetime.now(),
            signal_type=PdqSignal,
            signal_hash=pdq_hash,
            tags=["test_tag1", "test_tag2"],
        )

    def test_write_hash_record(self):
        """
        Test PipelineHashRecord write table with hardcode query
        """
        record = self.get_example_pdq_hash_record()

        record.write_to_table(self.table)

        result = self.table.get_item(
            Key={"PK": f"c#{TestPDQModels.TEST_CONTENT_ID}", "SK": "type#pdq"}
        )
        items = result.get("Item")
        content_hash = items.get("ContentHash")
        assert record.content_hash == content_hash

    def test_write_md5_hash_record(self):
        """
        Test PipelineHashRecord write table with hardcode query
        """
        record = self.get_example_md5_hash_record()

        record.write_to_table(self.table)

        result = self.table.get_item(
            Key={"PK": f"c#{TestPDQModels.TEST_CONTENT_ID}", "SK": "type#video_md5"}
        )
        items = result.get("Item")
        content_hash = items.get("ContentHash")
        assert record.content_hash == content_hash

    def test_query_hash_record(self):
        """
        Test PipelineHashRecord write table with get_from_content_key query
        """

        record = self.get_example_pdq_hash_record()
        record.write_to_table(self.table)

        assert any(
            [
                record == item
                for item in models.PipelineHashRecord.get_from_content_id(
                    self.table,
                    TestPDQModels.TEST_CONTENT_ID,
                    get_default_signal_type_mapping(),
                )
            ]
        )

    def test_query_md5_hash_record(self):
        record = self.get_example_md5_hash_record()
        record.write_to_table(self.table)

        assert any(
            [
                record == item
                for item in models.PipelineHashRecord.get_from_content_id(
                    self.table,
                    TestPDQModels.TEST_CONTENT_ID,
                    get_default_signal_type_mapping(),
                )
            ]
        )

    def test_query_recent_hash_records(self):
        record = self.get_example_pdq_hash_record()

        record.write_to_table(self.table)

        query_record = models.PipelineHashRecord.get_recent_items_page(
            self.table, get_default_signal_type_mapping()
        ).items[0]

        record.signal_specific_attributes = {}
        # While signal_specific_attributes are stored in the table, the index
        # does not store them. I do not think they need to either.

        assert record == query_record

    def test_write_match_record(self):
        """
        Test MatchRecord write table with hardcode query
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
        Test MatchRecord write table with get_from_content_key query
        """

        record = self.get_example_pdq_match_record()

        record.write_to_table(self.table)

        query_record = models.MatchRecord.get_from_content_id(
            self.table, TestPDQModels.TEST_CONTENT_ID, get_default_signal_type_mapping()
        )[0]

        assert record == query_record

    def test_query_match_record_by_signal_id(self):
        """
        Test MatchRecord write table with get_from_content_key query by signal
        """

        record = self.get_example_pdq_match_record()

        record.signal_specific_attributes = {}
        #  GSI-1: Signal ID index does not contain signal_specific attributes
        # yet. I'm not yet sure whether to include them.

        record.write_to_table(self.table)

        query_record = models.MatchRecord.get_from_signal(
            self.table,
            TestPDQModels.TEST_SIGNAL_ID,
            TestPDQModels.TEST_SIGNAL_SOURCE,
            get_default_signal_type_mapping(),
        )[0]

        assert record == query_record

    def test_query_match_recent_record(self):
        """
        Test MatchRecord write table with get_from_content_key query by recency
        """

        record = self.get_example_pdq_match_record()

        record.write_to_table(self.table)

        query_record = models.MatchRecord.get_recent_items_page(
            self.table, get_default_signal_type_mapping()
        ).items[0]

        record.signal_specific_attributes = {}
        # While signal_specific_attributes are stored in the table, the index
        # does not store them. I do not think they need to either.

        assert record == query_record

    def test_pdq_signal_metadata_manually(self):
        """
        Test PDQSignalMetadata write table
        """
        metadata = self.get_example_pdq_signal_metadata()

        metadata.write_to_table(self.table)

        result = self.table.get_item(
            Key={
                "PK": f"s#{ThreatExchangeSignalMetadata.SIGNAL_SOURCE_SHORTCODE}#{TestPDQModels.TEST_SIGNAL_ID}",
                "SK": f"{ThreatExchangeSignalMetadata.get_sort_key(TestPDQModels.TEST_DATASET_ID)}",
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

        query_metadata = ThreatExchangeSignalMetadata.get_from_signal(
            self.table, TestPDQModels.TEST_SIGNAL_ID, get_default_signal_type_mapping()
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

        query_metadata = ThreatExchangeSignalMetadata.get_from_signal(
            self.table, new_signal_id, get_default_signal_type_mapping()
        )[0]
        assert metadata.signal_hash == query_metadata.signal_hash
        for tag in metadata.tags:
            assert tag in query_metadata.tags

        replaced_tags = ["new", "list", "of", "tags"]
        metadata.tags = replaced_tags

        # second attmept at update should succeed
        assert metadata.update_tags_in_table_if_exists(self.table)
        query_metadata = ThreatExchangeSignalMetadata.get_from_signal(
            self.table,
            new_signal_id,
            get_default_signal_type_mapping(),
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

        query_metadata = ThreatExchangeSignalMetadata.get_from_signal(
            self.table,
            new_signal_id,
            get_default_signal_type_mapping(),
        )[0]
        assert metadata.signal_hash == query_metadata.signal_hash
        assert (
            PendingThreatExchangeOpinionChange.NONE.value
            == query_metadata.pending_opinion_change.value
        )

        metadata.pending_opinion_change = (
            PendingThreatExchangeOpinionChange.MARK_TRUE_POSITIVE
        )

        # second attmept at update should succeed
        assert metadata.update_pending_opinion_change_in_table_if_exists(self.table)
        query_metadata = ThreatExchangeSignalMetadata.get_from_signal(
            self.table, new_signal_id, get_default_signal_type_mapping()
        )[0]
        assert (
            PendingThreatExchangeOpinionChange.MARK_TRUE_POSITIVE.value
            == query_metadata.pending_opinion_change.value
        )
