# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import datetime
import typing as t
from dataclasses import dataclass, field
from mypy_boto3_dynamodb.service_resource import Table

"""
Data transfer object classes to be used with dynamodbstore
Classes in this module should implement methods `to_dynamodb_item(self)` and
`to_sqs_message(self)`
"""


class DynamoDBItem:
    def write_to_table(self, table: Table):
        table.put_item(Item=self.to_dynamodb_item())

    def to_dynamodb_item(self) -> t.Dict:
        raise NotImplementedError


@dataclass
class PDQRecordBase(DynamoDBItem):
    """
    Abstract Base Record for PDQ releated items.
    """

    SIGNAL_TYPE = "pdq"
    CONTENT_KEY_PREFIX = "c#"
    TYPE_PREFIX = "type#"

    content_key: str
    content_hash: str
    timestamp: datetime.datetime  # ISO-8601 formatted

    @staticmethod
    def get_dynamodb_content_key(key: str) -> str:
        return f"{PDQRecordBase.CONTENT_KEY_PREFIX}{key}"

    @staticmethod
    def get_dynamodb_type_key(key: str) -> str:
        return f"{PDQRecordBase.TYPE_PREFIX}{key}"

    def to_dynamodb_item(self) -> dict:
        raise NotImplementedError

    def to_sqs_message(self) -> dict:
        raise NotImplementedError


@dataclass
class PipelinePDQHashRecord(PDQRecordBase):
    """
    Successful execution at the hasher produces this record.
    """

    quality: int

    def to_dynamodb_item(self) -> dict:
        return {
            "PK": self.get_dynamodb_content_key(self.content_key),
            "SK": self.get_dynamodb_type_key(self.SIGNAL_TYPE),
            "ContentHash": self.content_hash,
            "Quality": self.quality,
            "Timestamp": self.timestamp.isoformat(),
            "HashType": self.SIGNAL_TYPE,
        }

    def to_sqs_message(self) -> dict:
        return {
            "hash": self.content_hash,
            "type": self.SIGNAL_TYPE,
            "key": self.content_key,
        }


@dataclass
class PDQMatchRecord(PDQRecordBase):
    """
    Successful execution at the matcher produces this record.
    """

    SIGNAL_KEY_PREFIX = "s#"
    signal_id: int
    signal_source: str
    signal_hash: str

    @staticmethod
    def get_dynamodb_signal_key(source: str, s_id: t.Union[str, int]) -> str:
        return f"{PDQMatchRecord.SIGNAL_KEY_PREFIX}{source}#{s_id}"

    def to_dynamodb_item(self) -> dict:
        return {
            "PK": self.get_dynamodb_content_key(self.content_key),
            "SK": self.get_dynamodb_signal_key(self.signal_source, self.signal_id),
            "ContentHash": self.content_hash,
            "Timestamp": self.timestamp.isoformat(),
            "SignalHash": self.signal_hash,
            "SignalSource": self.signal_source,
            "GSI1-PK": self.get_dynamodb_signal_key(self.signal_source, self.signal_id),
            "GSI1-SK": self.get_dynamodb_content_key(self.content_key),
            "HashType": self.SIGNAL_TYPE,
            "GSI2-PK": self.get_dynamodb_type_key(self.SIGNAL_TYPE),
        }

    def to_sqs_message(self) -> dict:
        # TODO add method for when matches are added to a sqs
        raise NotImplementedError
