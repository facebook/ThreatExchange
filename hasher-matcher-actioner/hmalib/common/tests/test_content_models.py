# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
from contextlib import contextmanager
from moto import mock_dynamodb2
from hmalib.common.content_models import (
    ContentObject,
    ActionEvent,
    ContentRefType,
    ContentType,
)
from hmalib.common.evaluator_models import ActionLabel, ActionRule
from hmalib.common.message_models import BankedSignal, ActionMessage
from hmalib.common.classification_models import ClassificationLabel
from hmalib.common.actioner_models import (
    WebhookPostActionPerformer,
)

import boto3
import datetime
import os


class TestContentModels(unittest.TestCase):
    table = None
    TEST_CONTENT_ID = "test_content_id_1"
    TEST_TIME = datetime.datetime(2021, 5, 17, 13, 38, 56, 965173)
    TEST_ACTION_LABEL = "TestEnqueueMiniCastleForReview"

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
            ],
            TableName=table_name,
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
        )

    @staticmethod
    def get_example_content_object():
        now = TestContentModels.TEST_TIME
        return ContentObject(
            content_id=TestContentModels.TEST_CONTENT_ID,
            content_type=ContentType.PHOTO,
            content_ref="key_of_s3_bucket_object_123",
            content_ref_type=ContentRefType.DEFAULT_S3_BUCKET,
            additional_fields={"additional", "ham"},
            submission_times=[now],
            created_at=now,
            updated_at=now,
        )  # .write_to_table(table)

    @staticmethod
    def get_example_action_event():
        enqueue_mini_castle_for_review_action_label = ActionLabel(
            TestContentModels.TEST_ACTION_LABEL
        )
        action_rules = [
            ActionRule(
                name="Enqueue Mini-Castle for Review",
                action_label=enqueue_mini_castle_for_review_action_label,
                must_have_labels=set(
                    [
                        ClassificationLabel("true_positive"),
                    ]
                ),
                must_not_have_labels=set(),
            ),
        ]

        banked_signal = BankedSignal(
            banked_content_id="4169895076385542",
            bank_id="303636684709969",
            bank_source="te",
        )
        banked_signal.add_classification("true_positive")

        action_performer = WebhookPostActionPerformer(
            name="EnqueueForReview",
            url="https://webhook.site/ff7ebc37-514a-439e-9a03-46f86989e195",
            headers='{"Connection":"keep-alive"}',
            # monitoring page:
            # https://webhook.site/#!/ff7ebc37-514a-439e-9a03-46f86989e195
        )

        action_message = ActionMessage(
            content_key=TestContentModels.TEST_CONTENT_ID,
            content_hash="361da9e6cf1b72f5cea0344e5bb6e70939f4c70328ace762529cac704297354a",
            matching_banked_signals=[banked_signal],
            action_label=enqueue_mini_castle_for_review_action_label,
            action_rules=action_rules,
        )

        return ActionEvent(
            content_id=action_message.content_key,
            performed_at=TestContentModels.TEST_TIME,
            action_label=action_message.action_label.value,
            action_performer=action_performer.to_aws_json(),
            action_rules=[rule.to_aws_json() for rule in action_message.action_rules],
        )  # .write_to_table(table)

    def test_write_content_object(self):
        """
        Test ContentObject's custom write_to_table
        """
        obj = self.get_example_content_object()
        obj.write_to_table(self.table)

        result = self.table.get_item(
            Key={
                "PK": f"c#{TestContentModels.TEST_CONTENT_ID}",
                "SK": "content_type#PHOTO",
            }
        )
        item = result.get("Item")
        AdditionalFields = item.get("AdditionalFields")
        CreatedOn = item.get("CreatedAt")
        assert AdditionalFields == obj.additional_fields
        assert TestContentModels.TEST_TIME.isoformat() == CreatedOn

    def test_write_action_event(self):
        """
        Test ActionEvent write
        """
        event = self.get_example_action_event()
        event.write_to_table(self.table)

        result = self.table.get_item(
            Key={
                "PK": f"c#{TestContentModels.TEST_CONTENT_ID}",
                "SK": f"action_time#{TestContentModels.TEST_TIME.isoformat()}",
            }
        )
        item = result.get("Item")
        action_label = item.get("ActionLabel")
        assert TestContentModels.TEST_ACTION_LABEL == action_label

    def test_query_content_object(self):
        """
        Test ContentObject write table with get_from_content_id query
        """
        obj = self.get_example_content_object()
        obj.write_to_table(self.table)

        query_obj = ContentObject.get_from_content_id(
            self.table, TestContentModels.TEST_CONTENT_ID
        )

        assert obj == query_obj

    def test_query_action_event(self):
        """
        Test ActionEvent write table with get_from_content_id query
        """

        event = self.get_example_action_event()
        event.write_to_table(self.table)

        query_event = ActionEvent.get_from_content_id(
            self.table, TestContentModels.TEST_CONTENT_ID
        )[0]

        assert event == query_event
