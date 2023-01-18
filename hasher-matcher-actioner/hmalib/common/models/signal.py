# Copyright (c) Meta Platforms, Inc. and affiliates.

r"""Signal Models

The structure of a signal and the data we want to retain on it is
super-dependent on the source of the signal. Trying to make a "base" signal
model can be futile because of the disparity of attributes and actions that
different sources can have.

Instead of abstracting out, for signals, we are creating separate models for
each source with their own feature evolution. This reality must also manifest on
the UI. eg. The actions you can take for threatexchange signals are distinct
from the actions you can take on your local bank's signals.

But, since the id-universes of the signals are distinct, how do we precisely
refer to a signal when using a signal id? This is a little complex because a
signal is uniquely defined by two of its attributes: `signal_source` and
`signal_id`.

So, every signal class needs to define a property `signal_source` which will be
used in indexing, queries etc.

When we add more signal sources, we'll understand the complexity and identify a
clean path for supporting multiple signal-sources. For now, only support
threatexchange.
"""

import datetime
from enum import Enum
import typing as t
from dataclasses import dataclass, field, asdict

from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr, Key, And
from botocore.exceptions import ClientError

from threatexchange.signal_type.signal_base import SignalType

from hmalib.common.mappings import HMASignalTypeMapping
from hmalib.common.models.models_base import DynamoDBItem


class PendingThreatExchangeOpinionChange(Enum):
    MARK_TRUE_POSITIVE = "mark_true_positive"
    MARK_FALSE_POSITIVE = "mark_false_positive"
    REMOVE_OPINION = "remove_opinion"
    NONE = "none"


@dataclass
class ThreatExchangeSignalMetadata(DynamoDBItem):
    """
    This object is designed to be an ~lookaside on some of the values used by
    MatchRecord for easier and more consistent updating by the syncer and UI.

    We only write these objects when we match against a signal from
    threatexchange. Updates can happen when:
      a. a user registers an opinion against this signal.
      b. the signal's attributes are updated in threatexchange.

    User's registration of an opinion is a multi-stage process. The opinion is
    first recorded on this object as a 'pending' opinion directly by the UI.
    Once the opinion is written to threatexchange and synced back, the 'pending'
    opinion is cleared.

    As clarified in the module's doc, it is okay to expose the threatexchange
    specific attribute 'privacy_group_id' because the capabilities that an
    exchange offers is going to be varied enough that abstracting might be
    impossible.

    Storage
    ---
    PK: s#{source_short_code}#{signal_id}
    SK: pg#{privacy_group_id}

    Where
    {source_short_code} = "te"
    and signal_id = {indicator_id} in threatexchange.
    and privacy_group_id is privacy_group_id in threatexchange.
    """

    SIGNAL_SOURCE_SHORTCODE = "te"
    PRIVACY_GROUP_PREFIX = "pg#"

    signal_id: str
    privacy_group_id: str
    updated_at: datetime.datetime
    signal_type: t.Type[SignalType]
    signal_hash: str
    tags: t.List[str] = field(default_factory=list)
    pending_opinion_change: PendingThreatExchangeOpinionChange = (
        PendingThreatExchangeOpinionChange.NONE
    )

    PROJECTION_EXPRESSION = "PK, SignalHash, SignalSource, SignalType, PrivacyGroup, Tags, PendingThreatExchangeOpinionChange, UpdatedAt"

    @classmethod
    def get_sort_key(self, privacy_group_id: str) -> str:
        return f"pg#{privacy_group_id}"

    def to_json(self) -> t.Dict:
        """
        Used by '/matches/for-hash' in lambdas/api/matches
        """
        result = asdict(self)
        result.update(
            signal_type=self.signal_type.get_name(),
            updated_at=self.updated_at.isoformat(),
            pending_opinion_change=self.pending_opinion_change.value,
        )
        return result

    def to_dynamodb_item(self) -> dict:
        return {
            "PK": self.get_dynamodb_signal_key(
                self.SIGNAL_SOURCE_SHORTCODE, self.signal_id
            ),
            "SK": self.get_sort_key(self.privacy_group_id),
            "SignalHash": self.signal_hash,
            "SignalSource": self.SIGNAL_SOURCE_SHORTCODE,
            "UpdatedAt": self.updated_at.isoformat(),
            "SignalType": self.signal_type.get_name(),
            "PrivacyGroup": self.privacy_group_id,
            "Tags": self.tags,
            "PendingThreatExchangeOpinionChange": self.pending_opinion_change.value,
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
            field_name="PendingThreatExchangeOpinionChange",
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
                        self.SIGNAL_SOURCE_SHORTCODE, self.signal_id
                    ),
                    "SK": self.get_sort_key(self.privacy_group_id),
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
        signal_type_mapping: HMASignalTypeMapping,
    ) -> t.List["ThreatExchangeSignalMetadata"]:
        """
        Load objects for this signal across all privacy groups. A signal_id,
        which maps to indicator_id on threatexchange, can be part of multiple
        privacy groups. Opinions are registered on a (privacy_group,
        indicator_id) tuple. Not exactly, but kind of.
        """
        pk = cls.get_dynamodb_signal_key(cls.SIGNAL_SOURCE_SHORTCODE, signal_id)

        items = table.query(
            KeyConditionExpression=Key("PK").eq(pk)
            & Key("SK").begins_with(cls.PRIVACY_GROUP_PREFIX),
            ProjectionExpression=cls.PROJECTION_EXPRESSION,
        ).get("Items")
        return cls._result_items_to_metadata(items or [], signal_type_mapping)

    @classmethod
    def get_from_signal_and_privacy_group(
        cls,
        table: Table,
        signal_id: t.Union[str, int],
        privacy_group_id: str,
        signal_type_mapping: HMASignalTypeMapping,
    ) -> t.Optional["ThreatExchangeSignalMetadata"]:
        """
        Load object for this signal and privacy_group combination.
        """
        pk = cls.get_dynamodb_signal_key(cls.SIGNAL_SOURCE_SHORTCODE, signal_id)
        sk = cls.get_sort_key(privacy_group_id)

        item = table.get_item(Key={"PK": pk, "SK": sk})
        return (
            "Item" in item
            and cls._result_item_to_metadata(item["Item"], signal_type_mapping)
            or None
        )

    @classmethod
    def _result_items_to_metadata(
        cls,
        items: t.List[t.Dict],
        signal_type_mapping: HMASignalTypeMapping,
    ) -> t.List["ThreatExchangeSignalMetadata"]:
        return [
            cls._result_item_to_metadata(item, signal_type_mapping) for item in items
        ]

    @classmethod
    def _result_item_to_metadata(
        cls,
        item: t.Dict,
        signal_type_mapping: HMASignalTypeMapping,
    ) -> "ThreatExchangeSignalMetadata":
        return ThreatExchangeSignalMetadata(
            signal_id=cls.remove_signal_key_prefix(item["PK"], item["SignalSource"]),
            privacy_group_id=item["PrivacyGroup"],
            updated_at=datetime.datetime.fromisoformat(item["UpdatedAt"]),
            signal_type=signal_type_mapping.get_signal_type_enforce(item["SignalType"]),
            signal_hash=item["SignalHash"],
            tags=item["Tags"],
            pending_opinion_change=PendingThreatExchangeOpinionChange(
                item.get(
                    "PendingThreatExchangeOpinionChange",
                    PendingThreatExchangeOpinionChange.NONE.value,
                )
            ),
        )
