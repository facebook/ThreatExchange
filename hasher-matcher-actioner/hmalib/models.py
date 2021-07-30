# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import datetime
import typing as t
from dataclasses import dataclass
from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

"""
Data transfer object classes to be used with dynamodbstore
Classes in this module should implement methods `to_dynamodb_item(self)` and
`to_sqs_message(self)`
"""


class DynamoDBItem:

    CONTENT_KEY_PREFIX = "c#"
    SIGNAL_KEY_PREFIX = "s#"
    TYPE_PREFIX = "type#"

    def write_to_table(self, table: Table):
        table.put_item(Item=self.to_dynamodb_item())

    def write_to_table_if_not_found(self, table: Table) -> bool:
        try:
            table.put_item(
                Item=self.to_dynamodb_item(),
                ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
            )
        except ClientError as client_error:
            # boto3 exception handling https://imgflip.com/i/5f5zfj
            if (
                client_error.response.get("Error", {"Code", "Unknown"}).get(
                    "Code", "Unknown"
                )
                == "ConditionalCheckFailedException"
            ):
                return False
            else:
                raise client_error
        return True

    def to_dynamodb_item(self) -> t.Dict:
        raise NotImplementedError

    @staticmethod
    def get_dynamodb_content_key(c_id: str) -> str:
        return f"{DynamoDBItem.CONTENT_KEY_PREFIX}{c_id}"

    @staticmethod
    def get_dynamodb_signal_key(source: str, s_id: t.Union[str, int]) -> str:
        return f"{DynamoDBItem.SIGNAL_KEY_PREFIX}{source}#{s_id}"

    @staticmethod
    def remove_signal_key_prefix(key: str, source: str) -> str:
        return key[len(DynamoDBItem.SIGNAL_KEY_PREFIX) + len(source) + 1 :]

    @staticmethod
    def get_dynamodb_type_key(type: str) -> str:
        return f"{DynamoDBItem.TYPE_PREFIX}{type}"

    @staticmethod
    def remove_content_key_prefix(key: str) -> str:
        return key[len(DynamoDBItem.CONTENT_KEY_PREFIX) :]


class AWSMessage:
    def to_aws_message(self) -> str:
        raise NotImplementedError

    @classmethod
    def from_aws_message(cls, message: str) -> "AWSMessage":
        raise NotImplementedError


@dataclass
class PDQRecordBase(DynamoDBItem):
    """
    Abstract Base Record for PDQ releated items.
    """

    SIGNAL_TYPE = "pdq"

    content_id: str
    content_hash: str
    updated_at: datetime.datetime

    def to_dynamodb_item(self) -> dict:
        raise NotImplementedError

    def to_sqs_message(self) -> dict:
        raise NotImplementedError

    @classmethod
    def get_from_time_range(
        cls, table: Table, start_time: str = None, end_time: str = None
    ) -> t.List:
        raise NotImplementedError


@dataclass
class PipelinePDQHashRecord(PDQRecordBase):
    """
    Successful execution at the hasher produces this record.
    """

    quality: int

    def to_dynamodb_item(self) -> dict:
        return {
            "PK": self.get_dynamodb_content_key(self.content_id),
            "SK": self.get_dynamodb_type_key(self.SIGNAL_TYPE),
            "ContentHash": self.content_hash,
            "Quality": self.quality,
            "UpdatedAt": self.updated_at.isoformat(),
            "HashType": self.SIGNAL_TYPE,
        }

    def to_sqs_message(self) -> dict:
        return {
            "hash": self.content_hash,
            "type": self.SIGNAL_TYPE,
            "key": self.content_id,
        }

    @classmethod
    def get_from_content_id(
        cls, table: Table, content_key: str
    ) -> t.Optional["PipelinePDQHashRecord"]:
        items = HashRecordQuery.from_content_key(
            table,
            cls.get_dynamodb_content_key(content_key),
            cls.get_dynamodb_type_key(cls.SIGNAL_TYPE),
        )
        records = cls._result_items_to_records(items)
        return None if not records else records[0]

    @classmethod
    def get_from_time_range(
        cls, table: Table, start_time: str = None, end_time: str = None
    ) -> t.List["PipelinePDQHashRecord"]:
        items = HashRecordQuery.from_time_range(
            table, cls.get_dynamodb_type_key(cls.SIGNAL_TYPE), start_time, end_time
        )
        return cls._result_items_to_records(items)

    @classmethod
    def _result_items_to_records(
        cls,
        items: t.List[t.Dict],
    ) -> t.List["PipelinePDQHashRecord"]:
        return [
            PipelinePDQHashRecord(
                content_id=item["PK"][len(cls.CONTENT_KEY_PREFIX) :],
                content_hash=item["ContentHash"],
                updated_at=datetime.datetime.fromisoformat(item["UpdatedAt"]),
                quality=item["Quality"],
            )
            for item in items
        ]


@dataclass
class PDQMatchRecord(PDQRecordBase):
    """
    Successful execution at the matcher produces this record.
    """

    signal_id: str
    signal_source: str
    signal_hash: str

    def to_dynamodb_item(self) -> dict:
        return {
            "PK": self.get_dynamodb_content_key(self.content_id),
            "SK": self.get_dynamodb_signal_key(self.signal_source, self.signal_id),
            "ContentHash": self.content_hash,
            "UpdatedAt": self.updated_at.isoformat(),
            "SignalHash": self.signal_hash,
            "SignalSource": self.signal_source,
            "GSI1-PK": self.get_dynamodb_signal_key(self.signal_source, self.signal_id),
            "GSI1-SK": self.get_dynamodb_content_key(self.content_id),
            "HashType": self.SIGNAL_TYPE,
            "GSI2-PK": self.get_dynamodb_type_key(self.SIGNAL_TYPE),
        }

    def to_sqs_message(self) -> dict:
        # TODO add method for when matches are added to a sqs
        raise NotImplementedError

    @classmethod
    def get_from_content_id(
        cls, table: Table, content_id: str
    ) -> t.List["PDQMatchRecord"]:
        items = MatchRecordQuery.from_content_key(
            table,
            cls.get_dynamodb_content_key(content_id),
            cls.SIGNAL_KEY_PREFIX,
            cls.SIGNAL_TYPE,
        )
        return cls._result_items_to_records(items)

    @classmethod
    def get_from_signal(
        cls, table: Table, signal_id: t.Union[str, int], signal_source: str
    ) -> t.List["PDQMatchRecord"]:
        items = MatchRecordQuery.from_signal_key(
            table,
            cls.get_dynamodb_signal_key(signal_source, signal_id),
            cls.SIGNAL_TYPE,
        )
        return cls._result_items_to_records(items)

    @classmethod
    def get_from_time_range(
        cls, table: Table, start_time: str = None, end_time: str = None
    ) -> t.List["PDQMatchRecord"]:
        items = MatchRecordQuery.from_time_range(
            table, cls.get_dynamodb_type_key(cls.SIGNAL_TYPE), start_time, end_time
        )
        return cls._result_items_to_records(items)

    @classmethod
    def _result_items_to_records(
        cls,
        items: t.List[t.Dict],
    ) -> t.List["PDQMatchRecord"]:
        return [
            PDQMatchRecord(
                content_id=cls.remove_content_key_prefix(item["PK"]),
                content_hash=item["ContentHash"],
                updated_at=datetime.datetime.fromisoformat(item["UpdatedAt"]),
                signal_id=cls.remove_signal_key_prefix(
                    item["SK"], item["SignalSource"]
                ),
                signal_source=item["SignalSource"],
                signal_hash=item["SignalHash"],
            )
            for item in items
        ]


class HashRecordQuery:
    DEFAULT_PROJ_EXP = "PK, ContentHash, UpdatedAt, Quality"

    @classmethod
    def from_content_key(
        cls, table: Table, content_key: str, hash_type_key: str = None
    ) -> t.List[t.Dict]:
        """
        Given a content key (and optional hash type), return its content hash (for that type).
        Written to be agnostic to hash type so it can be reused by other types of 'HashRecord's.
        """
        if hash_type_key is None:
            key_con_exp = Key("PK").eq(content_key) & Key("SK").begins_with(
                DynamoDBItem.SIGNAL_KEY_PREFIX
            )
        else:
            key_con_exp = Key("PK").eq(content_key) & Key("SK").eq(hash_type_key)

        return table.query(
            KeyConditionExpression=key_con_exp,
            ProjectionExpression=cls.DEFAULT_PROJ_EXP,
        ).get("Items", [])

    @classmethod
    def from_time_range(
        cls, table: Table, hash_type: str, start_time: str = None, end_time: str = None
    ) -> t.List[t.Dict]:
        """
        Given a hash type and time range, give me all the hashes found for that type and time range
        """
        if start_time is None:
            start_time = datetime.datetime.min.isoformat()
        if end_time is None:
            end_time = datetime.datetime.max.isoformat()
        return table.scan(
            FilterExpression=Key("SK").eq(hash_type)
            & Key("UpdatedAt").between(start_time, end_time),
            ProjectionExpression=cls.DEFAULT_PROJ_EXP,
        ).get("Items", [])


class MatchRecordQuery:

    """
    Written to be agnostic to hash type so it can be reused by other types of 'MatchRecord's.
    """

    DEFAULT_PROJ_EXP = (
        "PK, ContentHash, UpdatedAt, SK, SignalSource, SignalHash, Labels"
    )

    @classmethod
    def from_content_key(
        cls,
        table: Table,
        content_key: str,
        source_prefix: str = DynamoDBItem.SIGNAL_KEY_PREFIX,
        hash_type: str = None,
    ) -> t.List[t.Dict]:
        """
        Given a content key (and optional hash type), give me its content hash (for that type).

        """
        filter_exp = None
        if not hash_type is None:
            filter_exp = Attr("HashType").eq(hash_type)

        return table.query(
            KeyConditionExpression=Key("PK").eq(content_key)
            & Key("SK").begins_with(source_prefix),
            ProjectionExpression=cls.DEFAULT_PROJ_EXP,
            FilterExpression=filter_exp,
        ).get("Items", [])

    @classmethod
    def from_signal_key(
        cls,
        table: Table,
        signal_key: str,
        hash_type: str = None,
    ) -> t.List[t.Dict]:
        """
        Given a Signal ID/Key (and optional hash type), give me any content matches found
        """
        filter_exp = None
        if not hash_type is None:
            filter_exp = Attr("HashType").eq(hash_type)

        return table.query(
            IndexName="GSI-1",
            KeyConditionExpression=Key("GSI1-PK").eq(signal_key),
            ProjectionExpression=cls.DEFAULT_PROJ_EXP,
            FilterExpression=filter_exp,
        ).get("Items", [])

    @classmethod
    def from_time_range(
        cls, table: Table, hash_type: str, start_time: str = None, end_time: str = None
    ) -> t.List[t.Dict]:
        """
        Given a hash type and time range, give me all the matches found for that type and time range
        """
        if start_time is None:
            start_time = datetime.datetime.min.isoformat()
        if end_time is None:
            end_time = datetime.datetime.max.isoformat()
        return table.query(
            IndexName="GSI-2",
            KeyConditionExpression=Key("GSI2-PK").eq(hash_type)
            & Key("UpdatedAt").between(start_time, end_time),
            ProjectionExpression=cls.DEFAULT_PROJ_EXP,
        ).get("Items", [])
