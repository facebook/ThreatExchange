# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import datetime
import typing as t
import json
from dataclasses import dataclass, field
from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr, Key, And
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


class SNSMessage:
    def to_sns_message(self) -> str:
        raise NotImplementedError

    @classmethod
    def from_sns_message(cls, message: str) -> "SNSMessage":
        raise NotImplementedError


@dataclass
class SignalMetadataBase(DynamoDBItem):
    """
    Base for signal metadata.
    'ds' refers to dataset which for the time being is
    quivalent to collab or privacy group (and in the long term could map to bank)
    """

    DATASET_PREFIX = "ds#"

    signal_id: t.Union[str, int]
    ds_id: str
    updated_at: datetime.datetime
    signal_source: str
    signal_hash: str  # duplicated field with PDQMatchRecord having both for now to help with debuging/testing
    tags: t.List[str] = field(default_factory=list)

    @staticmethod
    def get_dynamodb_ds_key(ds_id: str) -> str:
        return f"{SignalMetadataBase.DATASET_PREFIX}{ds_id}"


@dataclass
class PDQSignalMetadata(SignalMetadataBase):
    """
    PDQ Signal metadata.
    This object is designed to be an ~lookaside on some of the values used by
    PDQMatchRecord for easier and more consistent updating by the syncer and UI.

    Otherwise updates on a signals metadata would require updating all
    PDQMatchRecord associated; TODO: For now there will be some overlap between
    this object and PDQMatchRecord.
    """

    SIGNAL_TYPE = "pdq"

    def to_dynamodb_item(self) -> dict:
        return {
            "PK": self.get_dynamodb_signal_key(self.signal_source, self.signal_id),
            "SK": self.get_dynamodb_ds_key(self.ds_id),
            "SignalHash": self.signal_hash,
            "SignalSource": self.signal_source,
            "UpdatedAt": self.updated_at.isoformat(),
            "HashType": self.SIGNAL_TYPE,
            "Tags": self.tags,
        }

    def update_tags_in_table_if_exists(self, table: Table) -> bool:
        """
        Only write tags for object in table if the objects with matchig PK and SK already exist
        (also updates updated_at).
        Returns true if object existed and therefore update was successful otherwise false.
        """
        try:
            table.update_item(
                Key={
                    "PK": self.get_dynamodb_signal_key(
                        self.signal_source, self.signal_id
                    ),
                    "SK": self.get_dynamodb_ds_key(self.ds_id),
                },
                # service_resource.Table.update_item's ConditionExpression params is not typed to use its own objects here...
                ConditionExpression=And(Attr("PK").exists(), Attr("SK").exists()),  # type: ignore
                ExpressionAttributeValues={
                    ":t": self.tags,
                    ":u": self.updated_at.isoformat(),
                },
                ExpressionAttributeNames={
                    "#T": "Tags",
                    "#U": "UpdatedAt",
                },
                UpdateExpression="SET #T = :t, #U = :u",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise e
            return False
        return True

    @classmethod
    def get_from_signal(
        cls,
        table: Table,
        signal_id: t.Union[str, int],
        signal_source: str,
    ) -> t.List["PDQSignalMetadata"]:

        items = table.query(
            KeyConditionExpression=Key("PK").eq(
                cls.get_dynamodb_signal_key(signal_source, signal_id)
            )
            & Key("SK").begins_with(cls.DATASET_PREFIX),
            ProjectionExpression="PK, ContentHash, UpdatedAt, SK, SignalSource, SignalHash, Tags",
            FilterExpression=Attr("HashType").eq(cls.SIGNAL_TYPE),
        ).get("Items", [])
        return cls._result_items_to_metadata(items)

    @classmethod
    def _result_items_to_metadata(
        cls,
        items: t.List[t.Dict],
    ) -> t.List["PDQSignalMetadata"]:
        return [
            PDQSignalMetadata(
                signal_id=cls.remove_signal_key_prefix(
                    item["PK"], item["SignalSource"]
                ),
                ds_id=item["SK"][len(cls.DATASET_PREFIX) :],
                updated_at=datetime.datetime.fromisoformat(item["UpdatedAt"]),
                signal_source=item["SignalSource"],
                signal_hash=item["SignalHash"],
                tags=item["Tags"],
            )
            for item in items
        ]


@dataclass
class Label:
    key: str
    value: str

    def to_dynamodb_dict(self) -> dict:
        return {"K": self.key, "V": self.value}

    @classmethod
    def from_dynamodb_dict(cls, d: dict) -> "Label":
        return cls(d["K"], d["V"])

    def __eq__(self, another_label: object) -> bool:
        if not isinstance(another_label, Label):
            return NotImplemented
        return self.key == another_label.key and self.value == another_label.value


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

    signal_id: t.Union[str, int]
    signal_source: str
    signal_hash: str
    labels: t.List[Label] = field(default_factory=list)

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
            "Labels": [x.to_dynamodb_dict() for x in self.labels],
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
                labels=[Label.from_dynamodb_dict(x) for x in item["Labels"]],
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


@dataclass
class MatchMessage(SNSMessage):
    """
    Captures a set of matches that will need to be processed. We create one
    match message for a single content key. It is possible that a single content
    hash matches multiple datasets. When it does, the entire set of matches are
    forwarded together so that any appropriate action can be taken.

    - `content_key`: A way for partners to refer uniquely to content on their
      site
    - `content_hash`: The hash generated for the content_key
    """

    content_key: str
    content_hash: str
    matching_banked_signals: t.List["BankedSignal"] = field(default_factory=list)

    def to_sns_message(self) -> str:
        return json.dumps(
            {
                "ContentKey": self.content_key,
                "ContentHash": self.content_hash,
                "BankedSignal": [x.to_dict() for x in self.matching_banked_signals],
            }
        )

    @classmethod
    def from_sns_message(cls, message: str) -> "MatchMessage":
        parsed = json.loads(message)
        return cls(
            parsed["ContentKey"],
            parsed["ContentHash"],
            [BankedSignal.from_dict(d) for d in parsed["BankedSignal"]],
        )


@dataclass
class BankedSignal:
    """
    BankedSignal fields:
    - `banked_content_id`: Inside the bank, the unique way to refer to what
      was matched against
    - `bank_id`: The unique way to refer to the bank banked_content_id came from
    - `bank_source`: This is forward looking: this might be 'te' or 'local';
      indicates source of or relationship between one or more banks
    - `classifications`: a list of strings that provide additional context
      about the banked signal
    """

    banked_content_id: str
    bank_id: str
    bank_source: str
    classifications: t.List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "BankedContentId": self.banked_content_id,
            "BankId": self.bank_id,
            "BankSource": self.bank_source,
            "Classifications": self.classifications,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BankedSignal":
        return cls(
            d["BankedContentId"], d["BankId"], d["BankSource"], d["Classifications"]
        )
