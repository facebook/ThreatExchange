# Copyright (c) Meta Platforms, Inc. and affiliates.

import datetime
import typing as t
from dataclasses import dataclass, field

from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Key

from threatexchange.signal_type.signal_base import SignalType

from hmalib.common.timebucketizer import CSViable
from hmalib.common.mappings import HMASignalTypeMapping
from hmalib.common.models.models_base import (
    DynamoDBItem,
    DynamoDBCursorKey,
    PaginatedResponse,
)

"""
Data transfer object classes to be used with dynamodbstore
Classes in this module should implement methods `to_dynamodb_item(self)` and
`to_sqs_message(self)`
"""


@dataclass
class PipelineRecordBase(DynamoDBItem):
    """
    Base Class for records of pieces of content going through the
    hashing/matching pipeline.
    """

    content_id: str

    signal_type: t.Type[SignalType]
    content_hash: str

    updated_at: datetime.datetime

    def to_dynamodb_item(self) -> dict:
        raise NotImplementedError

    def to_sqs_message(self) -> dict:
        raise NotImplementedError

    @classmethod
    def get_recent_items_page(
        cls,
        table: Table,
        signal_type_mapping: HMASignalTypeMapping,
        ExclusiveStartKey: t.Optional[DynamoDBCursorKey] = None,
    ) -> PaginatedResponse:
        """
        Get a paginated list of recent items. The API is purposefully kept
        """
        raise NotImplementedError


@dataclass
class PipelineRecordDefaultsBase:
    """
    Hash and match records may have signal_type specific attributes that are not
    universal. eg. PDQ hashes have quality and PDQ matches have distance while
    MD5 has neither. Assuming such signal_type specific attributes will not be
    indexed, we are choosing to put them into a bag of variables. See
    PipelineRecordBase.[de]serialize_signal_specific_attributes() to understand
    storage.

    Ideally, this would be an attribute with defaults, but that would make
    inheritance complicated because default_values would precede non-default
    values in the sub class.
    """

    signal_specific_attributes: t.Dict[str, t.Union[int, float, str]] = field(
        default_factory=dict
    )

    def serialize_signal_specific_attributes(self) -> dict:
        """
        Converts signal_specific_attributes into a dict. Uses the signal_type as
        a prefix.

        So for PDQ hash records, `item.signal_specific_attributes.quality` will
        become `item.pdq_quality`. Storing as top-level item attributes allows
        indexing if we need it later. You can't do that with nested elements.
        """
        # Note on Typing: PipelineRecordDefaultsBase is meant to be used with
        # PipelineRecordBase. So it will have access to all fields from
        # PipelineRecordBase. This is (impossible?) to express using mypy. So
        # ignore self.signal_type

        return {
            f"{self.signal_type.get_name()}_{key}": value  # type:ignore
            for key, value in self.signal_specific_attributes.items()
        }

    @staticmethod
    def _signal_specific_attribute_remove_prefix(prefix: str, k: str) -> str:
        return k[len(prefix) :]

    @classmethod
    def deserialize_signal_specific_attributes(
        cls, d: t.Dict[str, t.Any]
    ) -> t.Dict[str, t.Union[int, float, str]]:
        """
        Reverses serialize_signal_specific_attributes.
        """
        signal_type = d["SignalType"]
        signal_type_prefix = f"{signal_type}_"

        return {
            cls._signal_specific_attribute_remove_prefix(signal_type_prefix, key): value
            for key, value in d.items()
            if key.startswith(signal_type_prefix)
        }


@dataclass
class PipelineHashRecord(PipelineRecordDefaultsBase, PipelineRecordBase):
    """
    Successful execution at the hasher produces this record.
    """

    def to_dynamodb_item(self) -> dict:
        top_level_overrides = self.serialize_signal_specific_attributes()
        return dict(
            **top_level_overrides,
            **{
                "PK": self.get_dynamodb_content_key(self.content_id),
                "SK": self.get_dynamodb_type_key(self.signal_type.get_name()),
                "ContentHash": self.content_hash,
                "SignalType": self.signal_type.get_name(),
                "GSI2-PK": self.get_dynamodb_type_key(self.__class__.__name__),
                "UpdatedAt": self.updated_at.isoformat(),
            },
        )

    def to_legacy_sqs_message(self) -> dict:
        """
        Prior to supporting MD5, the hash message was simplistic and did not
        support all fields in the PipelineHashRecord. This is inconsistent with
        almost all other message models.

        We can remove this once pdq_hasher and pdq_matcher are removed.
        """
        return {
            "hash": self.content_hash,
            "type": self.signal_type.get_name(),
            "key": self.content_id,
        }

    def to_sqs_message(self) -> dict:
        return {
            "ContentId": self.content_id,
            "SignalType": self.signal_type.get_name(),
            "ContentHash": self.content_hash,
            "SignalSpecificAttributes": self.signal_specific_attributes,
            "UpdatedAt": self.updated_at.isoformat(),
        }

    @classmethod
    def from_sqs_message(
        cls, d: dict, signal_type_mapping: HMASignalTypeMapping
    ) -> "PipelineHashRecord":
        return cls(
            content_id=d["ContentId"],
            signal_type=signal_type_mapping.get_signal_type_enforce(d["SignalType"]),
            content_hash=d["ContentHash"],
            signal_specific_attributes=d["SignalSpecificAttributes"],
            updated_at=datetime.datetime.fromisoformat(d["UpdatedAt"]),
        )

    @classmethod
    def could_be(cls, d: dict) -> bool:
        """
        Return True if this dict can be converted to a PipelineHashRecord
        """
        return "ContentId" in d and "SignalType" in d and "ContentHash" in d

    @classmethod
    def get_from_content_id(
        cls,
        table: Table,
        content_id: str,
        signal_type_mapping: HMASignalTypeMapping,
        signal_type: t.Optional[t.Type[SignalType]] = None,
    ) -> t.List["PipelineHashRecord"]:
        """
        Returns all available PipelineHashRecords for a content_id.
        """
        expected_pk = cls.get_dynamodb_content_key(content_id)

        if signal_type is None:
            condition_expression = Key("PK").eq(expected_pk) & Key("SK").begins_with(
                DynamoDBItem.TYPE_PREFIX
            )
        else:
            condition_expression = Key("PK").eq(expected_pk) & Key("SK").eq(
                DynamoDBItem.get_dynamodb_type_key(signal_type.get_name())
            )

        return cls._result_items_to_records(
            table.query(
                KeyConditionExpression=condition_expression,
            ).get("Items", []),
            signal_type_mapping=signal_type_mapping,
        )

    @classmethod
    def get_recent_items_page(
        cls,
        table: Table,
        signal_type_mapping: HMASignalTypeMapping,
        exclusive_start_key: t.Optional[DynamoDBCursorKey] = None,
    ) -> PaginatedResponse["PipelineHashRecord"]:
        """
        Get a paginated list of recent items.
        """
        if not exclusive_start_key:
            # Evidently, https://github.com/boto/boto3/issues/2813 boto is able
            # to distinguish fun(Parameter=None) from fun(). So, we can't use
            # exclusive_start_key's optionality. We have to do an if clause!
            # Fun!
            result = table.query(
                IndexName="GSI-2",
                ScanIndexForward=False,
                Limit=100,
                KeyConditionExpression=Key("GSI2-PK").eq(
                    DynamoDBItem.get_dynamodb_type_key(cls.__name__)
                ),
            )
        else:
            result = table.query(
                IndexName="GSI-2",
                ExclusiveStartKey=exclusive_start_key,
                ScanIndexForward=False,
                Limit=100,
                KeyConditionExpression=Key("GSI2-PK").eq(
                    DynamoDBItem.get_dynamodb_type_key(cls.__name__)
                ),
            )

        return PaginatedResponse(
            t.cast(DynamoDBCursorKey, result.get("LastEvaluatedKey", None)),
            cls._result_items_to_records(
                result["Items"], signal_type_mapping=signal_type_mapping
            ),
        )

    @classmethod
    def _result_items_to_records(
        cls,
        items: t.List[t.Dict],
        signal_type_mapping: HMASignalTypeMapping,
    ) -> t.List["PipelineHashRecord"]:
        """
        Get a paginated list of recent hash records. Subsequent calls must use
        `return_value.last_evaluated_key`.
        """
        return [
            PipelineHashRecord(
                content_id=item["PK"][len(cls.CONTENT_KEY_PREFIX) :],
                signal_type=signal_type_mapping.get_signal_type_enforce(
                    item["SignalType"]
                ),
                content_hash=item["ContentHash"],
                updated_at=datetime.datetime.fromisoformat(item["UpdatedAt"]),
                signal_specific_attributes=cls.deserialize_signal_specific_attributes(
                    item
                ),
            )
            for item in items
        ]


@dataclass
class _MatchRecord(PipelineRecordBase):
    """
    Successful execution at the matcher produces this record.
    """

    signal_id: str
    signal_source: str
    signal_hash: str
    match_distance: t.Optional[int] = None


@dataclass
class MatchRecord(PipelineRecordDefaultsBase, _MatchRecord):
    """
    Weird, innit? You can't introduce non-default fields after default fields.
    All default fields in PipelineRecordBase are actually in
    PipelineRecordDefaultsBase and this complex inheritance chain allows you to
    create an MRO that is legal.

    H/T:
    https://stackoverflow.com/questions/51575931/class-inheritance-in-python-3-7-dataclasses
    """

    def to_dynamodb_item(self) -> dict:
        top_level_overrides = self.serialize_signal_specific_attributes()
        return dict(
            **top_level_overrides,
            **{
                "PK": self.get_dynamodb_content_key(self.content_id),
                "SK": self.get_dynamodb_signal_key(self.signal_source, self.signal_id),
                "ContentHash": self.content_hash,
                "UpdatedAt": self.updated_at.isoformat(),
                "SignalHash": self.signal_hash,
                "SignalSource": self.signal_source,
                "SignalType": self.signal_type.get_name(),
                "GSI1-PK": self.get_dynamodb_signal_key(
                    self.signal_source, self.signal_id
                ),
                "GSI1-SK": self.get_dynamodb_content_key(self.content_id),
                "HashType": self.signal_type.get_name(),
                "GSI2-PK": self.get_dynamodb_type_key(self.__class__.__name__),
                "MatchDistance": self.match_distance,
            },
        )

    def to_sqs_message(self) -> dict:
        # TODO add method for when matches are added to a sqs
        raise NotImplementedError

    @classmethod
    def get_from_content_id(
        cls, table: Table, content_id: str, signal_type_mapping: HMASignalTypeMapping
    ) -> t.List["MatchRecord"]:
        """
        Return all matches for a content_id.
        """

        content_key = DynamoDBItem.get_dynamodb_content_key(content_id)
        source_prefix = DynamoDBItem.SIGNAL_KEY_PREFIX

        return cls._result_items_to_records(
            table.query(
                KeyConditionExpression=Key("PK").eq(content_key)
                & Key("SK").begins_with(source_prefix),
            ).get("Items", []),
            signal_type_mapping,
        )

    @classmethod
    def get_from_signal(
        cls,
        table: Table,
        signal_id: t.Union[str, int],
        signal_source: str,
        signal_type_mapping: HMASignalTypeMapping,
    ) -> t.List["MatchRecord"]:
        """
        Return all matches for a signal. Needs source and id to uniquely
        identify a signal.
        """

        signal_key = DynamoDBItem.get_dynamodb_signal_key(signal_source, signal_id)

        return cls._result_items_to_records(
            table.query(
                IndexName="GSI-1",
                KeyConditionExpression=Key("GSI1-PK").eq(signal_key),
            ).get("Items", []),
            signal_type_mapping,
        )

    @classmethod
    def get_recent_items_page(
        cls,
        table: Table,
        signal_type_mapping: HMASignalTypeMapping,
        exclusive_start_key: t.Optional[DynamoDBCursorKey] = None,
    ) -> PaginatedResponse["MatchRecord"]:
        """
        Get a paginated list of recent match records. Subsequent calls must use
        `return_value.last_evaluated_key`.
        """
        if not exclusive_start_key:
            # Evidently, https://github.com/boto/boto3/issues/2813 boto is able
            # to distinguish fun(Parameter=None) from fun(). So, we can't use
            # exclusive_start_key's optionality. We have to do an if clause!
            # Fun!
            result = table.query(
                IndexName="GSI-2",
                Limit=100,
                ScanIndexForward=False,
                KeyConditionExpression=Key("GSI2-PK").eq(
                    DynamoDBItem.get_dynamodb_type_key(cls.__name__)
                ),
            )
        else:
            result = table.query(
                IndexName="GSI-2",
                Limit=100,
                ExclusiveStartKey=exclusive_start_key,
                ScanIndexForward=False,
                KeyConditionExpression=Key("GSI2-PK").eq(
                    DynamoDBItem.get_dynamodb_type_key(cls.__name__)
                ),
            )

        return PaginatedResponse(
            t.cast(DynamoDBCursorKey, result.get("LastEvaluatedKey", None)),
            cls._result_items_to_records(
                result["Items"], signal_type_mapping=signal_type_mapping
            ),
        )

    @classmethod
    def _result_items_to_records(
        cls,
        items: t.List[t.Dict],
        signal_type_mapping: HMASignalTypeMapping,
    ) -> t.List["MatchRecord"]:
        return [
            MatchRecord(
                content_id=cls.remove_content_key_prefix(item["PK"]),
                content_hash=item["ContentHash"],
                updated_at=datetime.datetime.fromisoformat(item["UpdatedAt"]),
                signal_type=signal_type_mapping.get_signal_type_enforce(
                    item["SignalType"]
                ),
                signal_id=cls.remove_signal_key_prefix(
                    item["SK"], item["SignalSource"]
                ),
                signal_source=item["SignalSource"],
                signal_hash=item["SignalHash"],
                signal_specific_attributes=cls.deserialize_signal_specific_attributes(
                    item
                ),
                match_distance=item.get("MatchDistance"),
            )
            for item in items
        ]


@dataclass(eq=True)
class HashRecord(CSViable):
    """
    We are getting these records, with content_hashes and content_ids from the hashing process with intent to build an PDQIndex
    """

    content_hash: str
    content_id: str

    def to_csv(self) -> t.List[t.Union[str, int]]:
        return [self.content_hash, self.content_id]

    @classmethod
    def from_csv(cls: t.Type["HashRecord"], value: t.List[str]) -> "HashRecord":
        return HashRecord(value[0], value[1])
