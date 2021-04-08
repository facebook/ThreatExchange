# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import datetime
import typing as t
import json
from dataclasses import dataclass, field
from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr, Key

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
class Label:
    key: str
    value: str

    def to_dynamodb_dict(self) -> dict:
        return {"K": self.key, "V": self.value}

    @classmethod
    def from_dynamodb_dict(cls, d: dict) -> "Label":
        return cls(d["K"], d["V"])


@dataclass
class PDQRecordBase(DynamoDBItem):
    """
    Abstract Base Record for PDQ releated items.
    """

    SIGNAL_TYPE = "pdq"

    content_id: str
    content_hash: str
    updated_at: datetime.datetime  # ISO-8601 formatted

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
        records = [
            PipelinePDQHashRecord(
                item["PK"][len(DynamoDBItem.CONTENT_KEY_PREFIX) :],
                item["ContentHash"],
                datetime.datetime.fromisoformat(item["UpdatedAt"]),
                item["Quality"],
            )
            for item in items
        ]
        return None if not records else records[0]


@dataclass
class PDQMatchRecord(PDQRecordBase):
    """
    Successful execution at the matcher produces this record.
    """

    signal_id: t.Union[str, int]
    signal_source: str
    signal_hash: str
    labels: t.List[Label] = field(default_factory=list)

    @staticmethod
    def get_dynamodb_signal_key(source: str, s_id: t.Union[str, int]) -> str:
        return f"{PDQMatchRecord.SIGNAL_KEY_PREFIX}{source}#{s_id}"

    @staticmethod
    def remove_signal_key_prefix(key: str, source: str) -> str:
        return key[len(PDQMatchRecord.SIGNAL_KEY_PREFIX) + len(source) + 1 :]

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

    @staticmethod
    def _result_items_to_records(
        items: t.List[t.Dict],
    ) -> t.List["PDQMatchRecord"]:
        return [
            PDQMatchRecord(
                PDQMatchRecord.remove_content_key_prefix(item["PK"]),
                item["ContentHash"],
                datetime.datetime.fromisoformat(item["UpdatedAt"]),
                PDQMatchRecord.remove_signal_key_prefix(
                    item["SK"], item["SignalSource"]
                ),
                item["SignalSource"],
                item["SignalHash"],
                [Label.from_dynamodb_dict(x) for x in item["Labels"]],
            )
            for item in items
        ]


class HashRecordQuery:
    @staticmethod
    def from_content_key(
        table: Table, content_key: str, hash_type_key: str = None
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
            ProjectionExpression="PK, ContentHash, UpdatedAt, Quality",
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
    forwarded together so that *one* appropriate action can be taken.

    - `content_key`: A way for partners to refer uniquely to content on their
      site
    - `content_hash`: The hash generated for the content_key
    """

    content_key: str
    content_hash: str
    match_details: t.List["DatasetMatchDetails"] = field(default_factory=list)

    def to_sns_message(self) -> str:
        return json.dumps(
            {
                "ContentKey": self.content_key,
                "ContentHash": self.content_hash,
                "MatchDetails": [x.to_dict() for x in self.match_details],
            }
        )

    @classmethod
    def from_sns_message(cls, message: str) -> "MatchMessage":
        parsed = json.loads(message)
        return cls(
            parsed["ContentKey"],
            parsed["ContentHash"],
            [DatasetMatchDetails.from_dict(d) for d in parsed["MatchDetails"]],
        )


@dataclass
class DatasetMatchDetails:
    """
    Dataset fields:
    - `banked_content_id`: Inside the bank, what's a unique way to refer to what
      was matched against?
    - `bank_id`: [optional][Defaults to 'threatexchange_all_collabs'] Which bank
      did we fetch this banked_content from?
    - `bank_source`: [optional][Defaults to 'api/threatexchange'] This is
      forward looking, but potentially, we could have this be 'local', or
      'api/some-other-api'
    """

    banked_indicator_id: str

    # source information, for now, it's okay to be hardcoded
    # to threatexchange
    bank_id: str = "threatexchange_all_collabs"
    bank_source: str = "api/threatexchange"

    def to_dict(self) -> dict:
        return {
            "BankedIndicatorId": self.banked_indicator_id,
            "BankId": self.bank_id,
            "BankSource": self.bank_source,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DatasetMatchDetails":
        return cls(
            d["BankedIndicatorId"],
            d["BankId"],
            d["BankSource"],
        )
