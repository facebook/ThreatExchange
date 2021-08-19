# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import datetime
from enum import Enum
import typing as t

from dataclasses import dataclass, field, asdict
from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr, Key, And
from botocore.exceptions import ClientError

from hmalib.models import DynamoDBItem


class PendingOpinionChange(Enum):
    MARK_TRUE_POSITIVE = "mark_true_positive"
    MARK_FALSE_POSITIVE = "mark_false_positive"
    REMOVE_OPINION = "remove_opinion"
    NONE = "none"


@dataclass
class SignalMetadataBase(DynamoDBItem):
    """
    Base for signal metadata.
    'ds' refers to dataset which for the time being is
    quivalent to collab or privacy group (and in the long term could map to bank)
    """

    DATASET_PREFIX = "ds#"

    signal_id: str
    ds_id: str
    updated_at: datetime.datetime
    signal_source: str
    signal_hash: str  # duplicated field with PDQMatchRecord having both for now to help with debuging/testing
    tags: t.List[str] = field(default_factory=list)
    pending_opinion_change: PendingOpinionChange = PendingOpinionChange.NONE

    @staticmethod
    def get_dynamodb_ds_key(ds_id: str) -> str:
        return f"{SignalMetadataBase.DATASET_PREFIX}{ds_id}"

    def to_json(self) -> t.Dict:
        """
        Used by '/matches/for-hash' in lambdas/api/matches
        """
        result = asdict(self)
        result.update(
            updated_at=self.updated_at.isoformat(),
            pending_opinion_change=self.pending_opinion_change.value,
        )
        return result


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
            "PendingOpinionChange": self.pending_opinion_change.value,
        }

    def update_tags_in_table_if_exists(self, table: Table) -> bool:
        return self._update_field_in_table_if_exists(
            table,
            field_value=self.tags,
            field_name="Tags",
        )

    def update_pending_opinion_change_in_table_if_exists(self, table: Table) -> bool:
        return self._update_field_in_table_if_exists(
            table,
            field_value=self.pending_opinion_change.value,
            field_name="PendingOpinionChange",
        )

    def _update_field_in_table_if_exists(
        self, table: Table, field_value: t.Any, field_name: str
    ) -> bool:
        """
        Only write the field for object in table if the objects with matchig PK and SK already exist
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
                    ":f": field_value,
                    ":u": self.updated_at.isoformat(),
                },
                ExpressionAttributeNames={
                    "#F": field_name,
                    "#U": "UpdatedAt",
                },
                UpdateExpression="SET #F = :f, #U = :u",
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
        """
        Load the metadata objects relaed to this signal.
        Optionally provide a data set id to filter to
        """
        items = table.query(
            KeyConditionExpression=Key("PK").eq(
                cls.get_dynamodb_signal_key(signal_source, signal_id)
            )
            & Key("SK").begins_with(cls.DATASET_PREFIX),
            FilterExpression=Attr("HashType").eq(cls.SIGNAL_TYPE),
            ProjectionExpression="PK, ContentHash, UpdatedAt, SK, SignalSource, SignalHash, Tags, PendingOpinionChange",
        ).get("Items", [])
        return cls._result_items_to_metadata(items)

    @classmethod
    def get_from_signal_and_ds_id(
        cls, table: Table, signal_id: t.Union[str, int], signal_source: str, ds_id: str
    ) -> t.Optional["PDQSignalMetadata"]:
        item = table.get_item(
            Key={
                "PK": cls.get_dynamodb_signal_key(signal_source, signal_id),
                "SK": cls.DATASET_PREFIX + ds_id,
            },
        ).get("Item")
        return cls._result_item_to_metadata(item) if item else None

    @classmethod
    def _result_items_to_metadata(
        cls,
        items: t.List[t.Dict],
    ) -> t.List["PDQSignalMetadata"]:
        return [cls._result_item_to_metadata(item) for item in items]

    @classmethod
    def _result_item_to_metadata(
        cls,
        item: t.Dict,
    ) -> "PDQSignalMetadata":
        return PDQSignalMetadata(
            signal_id=cls.remove_signal_key_prefix(item["PK"], item["SignalSource"]),
            ds_id=item["SK"][len(cls.DATASET_PREFIX) :],
            updated_at=datetime.datetime.fromisoformat(item["UpdatedAt"]),
            signal_source=item["SignalSource"],
            signal_hash=item["SignalHash"],
            tags=item["Tags"],
            pending_opinion_change=PendingOpinionChange(
                item.get("PendingOpinionChange", PendingOpinionChange.NONE.value)
            ),
        )
