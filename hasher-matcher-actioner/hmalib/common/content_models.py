# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import datetime
from enum import Enum
import typing as t

from dataclasses import dataclass, field, asdict
from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr, Key, Or
from botocore.exceptions import ClientError

from hmalib.lambdas.api.middleware import JSONifiable
from hmalib.models import DynamoDBItem


@dataclass
class ContentObjectBase(DynamoDBItem):
    """
    Base content obeject for ActionRecords and ContentObjects
    Both of which used content_id as there PK
    (This is similar to Hash and Match Records
    but can easily be moved to it's own db table as they do not
    use the other indexes)
    """

    content_id: str


@dataclass
class ActionEvent(ContentObjectBase, JSONifiable):
    """
    Record of action events in the action performer
    keyed based on action_label and time of event.
    For the time being the action_rules in the action message
    being preformed are also stored as a list serialized json blobs
    """

    ACTION_TIME_PREFIX = "action_time#"
    DEFAULT_PROJ_EXP = "PK, SK, ActionLabel, ActionPerformer, ActionRules"

    performed_at: datetime.datetime
    action_label: str
    action_performer: str
    action_rules: t.List[str]

    @staticmethod
    def get_dynamodb_action_time_key(performed_at: datetime.datetime) -> str:
        return f"{ActionEvent.ACTION_TIME_PREFIX}{performed_at.isoformat()}"

    def to_dynamodb_item(self) -> dict:
        return {
            "PK": self.get_dynamodb_content_key(self.content_id),
            "SK": self.get_dynamodb_action_time_key(self.performed_at),
            "ActionLabel": self.action_label,
            "ActionPerformer": self.action_performer,
            "ActionRules": self.action_rules,
        }

    def to_json(self) -> t.Dict:
        """
        Used by '/content/action-history/<content-id>' in lambdas/api/content
        """
        result = asdict(self)
        result.update(performed_at=self.performed_at.isoformat())
        return result

    @classmethod
    def get_from_content_id(
        cls,
        table: Table,
        content_id: str,
    ) -> t.List["ActionEvent"]:

        items = table.query(
            KeyConditionExpression=Key("PK").eq(
                cls.get_dynamodb_content_key(content_id)
            )
            & Key("SK").begins_with(cls.ACTION_TIME_PREFIX),
            ProjectionExpression=cls.DEFAULT_PROJ_EXP,
        ).get("Items", [])

        return cls._result_item_to_action_event(items)

    @classmethod
    def _result_item_to_action_event(
        cls,
        items: t.List[t.Dict],
    ) -> t.List["ActionEvent"]:
        return [
            ActionEvent(
                content_id=cls.remove_content_key_prefix(
                    item["PK"],
                ),
                performed_at=datetime.datetime.fromisoformat(
                    item["SK"][len(cls.ACTION_TIME_PREFIX) :]
                ),
                action_label=item["ActionLabel"],
                action_performer=item["ActionPerformer"],
                action_rules=item["ActionRules"],
            )
            for item in items
        ]


@dataclass
class ContentObject(ContentObjectBase, JSONifiable):
    """
    Content object that stores the values related to a specific
    content_id and content_type.
    Note/TODO: Something like an override flag should be added to the submit API
    as ContentRef equality check on bytes is impractical so instead
    something like:
     "This content_id exists, [x] overwrite? (I know what you're doing)"
    is likely better.
    """

    CONTENT_TYPE_PREFIX = "content_type#"

    content_type: str
    content_ref: str
    content_ref_type: str
    submission_times: t.List[datetime.datetime]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_fields: t.Set[str] = field(default_factory=set)

    @staticmethod
    def get_dynamodb_content_type_key(content_type: str) -> str:
        return f"{ContentObject.CONTENT_TYPE_PREFIX}{content_type}"

    def to_json(self) -> t.Dict:
        """
        Used by '/content/<content-id>' in lambdas/api/content
        """
        result = asdict(self)
        result.update(
            additional_fields=list(
                self.additional_fields if self.additional_fields else set()
            ),
            submission_times=[s.isoformat() for s in self.submission_times],
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat(),
        )
        return result

    def write_to_table(self, table: Table):
        """
        Write operations for this object need to be special cased (to avoid overwritting)
        Therefore we do not implement `to_dynamodb_item`

        If you're curious it would ~look like this:
        def to_dynamodb_item(self) -> dict:
            return {
                "PK": self.get_dynamodb_content_key(self.content_id),
                "SK": self.get_dynamodb_content_type_key(self.content_type),
                "ContentRef": self.content_ref,
                "ContentRefType": self.content_ref_type,
                "AdditionalFields": self.additional_fields,
                "SubmissionTimes": [s.isoformat() for s in self.submission_times],
                "CreatedOn": self.created_at.isoformat(),
                "UpdatedAt": self.updated_at.isoformat(),
            }
        """
        # put_item does not support UpdateExpression
        table.update_item(
            Key={
                "PK": self.get_dynamodb_content_key(self.content_id),
                "SK": self.get_dynamodb_content_type_key(self.content_type),
            },
            # If ContentRef exists it needs to match or BAD THING(tm) can happen...
            ConditionExpression=Or(Attr("ContentRef").not_exists(), Attr("ContentRef").eq(self.content_ref)),  # type: ignore
            # Unfortunately while prod is happy with this on multiple lines pytest breaks...
            UpdateExpression="""SET ContentRef = :cr, ContentRefType = :crt, SubmissionTimes = list_append(if_not_exists(SubmissionTimes, :empty_list), :s), CreatedAt = if_not_exists(CreatedAt, :c), UpdatedAt = :u ADD AdditionalFields :af""",
            ExpressionAttributeValues={
                ":cr": self.content_ref,
                ":crt": self.content_ref_type,
                ":af": self.additional_fields
                if self.additional_fields
                else {"Placeholder"},
                ":s": [s.isoformat() for s in self.submission_times],
                ":c": self.created_at.isoformat(),
                ":u": self.updated_at.isoformat(),
                ":empty_list": [],
            },
        )

    @classmethod
    def get_from_content_id(
        cls,
        table: Table,
        content_id: str,
        content_type: str = "PHOTO",
    ) -> t.Optional["ContentObject"]:
        if not content_id:
            return None
        item = table.get_item(
            Key={
                "PK": cls.get_dynamodb_content_key(content_id),
                "SK": cls.get_dynamodb_content_type_key(content_type),
            }
        ).get("Item", None)
        if item:
            return cls._result_item_to_object(item)
        return None

    @classmethod
    def _result_item_to_object(
        cls,
        item: t.Dict,
    ) -> "ContentObject":
        return ContentObject(
            content_id=cls.remove_content_key_prefix(
                item["PK"],
            ),
            content_type=item["SK"][len(cls.CONTENT_TYPE_PREFIX) :],
            content_ref=item["ContentRef"],
            content_ref_type=item["ContentRefType"],
            additional_fields=item["AdditionalFields"],
            # Notes careful not using this version to write back to the table...
            # Will dup previous submissions...
            submission_times=[
                datetime.datetime.fromisoformat(s) for s in item["SubmissionTimes"]
            ],
            created_at=datetime.datetime.fromisoformat(item["CreatedAt"]),
            updated_at=datetime.datetime.fromisoformat(item["UpdatedAt"]),
        )
