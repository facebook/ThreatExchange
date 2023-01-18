# Copyright (c) Meta Platforms, Inc. and affiliates.

import datetime
from enum import Enum
from multiprocessing.sharedctypes import Value
import typing as t

from dataclasses import dataclass, field, asdict
from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr, Key, Or
from botocore.exceptions import ClientError

from threatexchange.content_type.content_base import ContentType

from hmalib.lambdas.api.middleware import JSONifiable
from hmalib.common.mappings import HMASignalTypeMapping
from hmalib.common.models.models_base import DynamoDBItem


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


class ContentRefType(Enum):
    """
    How must we get follow the content-ref. Where is this content stored?
    """

    # Stored in HMA owned default S3 bucket. ContentRef only needs key
    DEFAULT_S3_BUCKET = "DEFAULT_S3_BUCKET"

    # Stored outside of HMA, only ref is a URL
    URL = "URL"

    # Stored in an S3 bucket not owned by HMA. Has considerable overlap with
    # URL, but explicit is better than implicit. ContentRef would need key and
    # bucket.
    S3_BUCKET = "S3_BUCKET"

    # No content ref was provided for the submission
    NONE = "NONE"


@dataclass
class ContentObject(ContentObjectBase, JSONifiable):
    """
    Content object that stores the values related to a specific
    content_id and content_type.

    TODO: Something like an override flag should be added to the submit API
    as ContentRef equality check on bytes is impractical so instead
    something like:
     "This content_id exists, [x] overwrite? (I know what you're doing)"
    is likely better.
    """

    CONTENT_STATIC_SK = "#content_object"

    # Because of the way update expressions work with `ADD` for sets
    # if an empty set is given to additional fields it will error
    # which is a shame because otherwise `ADD` is exactly what we want.
    # the addition and (removal) of this placeholder when translating to
    # (and from) ddb gets around this.
    ADDITIONAL_FIELDS_PLACE_HOLDER = "_ADDITIONAL_FIELDS_PLACE_HOLDER"

    # Is this a photo, a video, a piece of text? etc.
    content_type: t.Type[ContentType]

    # Raw value of the content reference. eg. An s3 url, s3 key, url
    content_ref: str

    # How must the content be followed, eg to download for hashing, to render a
    # preview, etc.
    content_ref_type: ContentRefType

    submission_times: t.List[datetime.datetime]

    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_fields: t.Set[str] = field(default_factory=set)

    @staticmethod
    def get_dynamodb_content_type_key() -> str:
        return ContentObject.CONTENT_STATIC_SK

    def to_json(self) -> t.Dict:
        """
        Used by '/content/<content-id>' in lambdas/api/content
        """
        result = asdict(self)
        result.update(
            additional_fields=list(
                self.additional_fields if self.additional_fields else set()
            ),
            content_type=self.content_type.get_name(),
            content_ref_type=self.content_ref_type.value,
            submission_times=[s.isoformat() for s in self.submission_times],
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat(),
        )
        return result

    def write_to_table(self, table: Table):
        """
        Write operations for this object need to be special cased (to avoid overwritting)
        Therefore we do not implement `to_dynamodb_item` however basically the body of that
        method is used in this class's impl of `write_to_table_if_not_found`
        """
        # put_item does not support UpdateExpression
        table.update_item(
            Key={
                "PK": self.get_dynamodb_content_key(self.content_id),
                "SK": self.get_dynamodb_content_type_key(),
            },
            # If ContentRef exists it needs to match or BAD THING(tm) can happen...
            ConditionExpression=Or(Attr("ContentRef").not_exists(), Attr("ContentRef").eq(self.content_ref)),  # type: ignore
            # Unfortunately while prod is happy with this on multiple lines pytest breaks...
            UpdateExpression="""SET ContentType = :ct, ContentRef = :cr, ContentRefType = :crt, SubmissionTimes = list_append(if_not_exists(SubmissionTimes, :empty_list), :s), CreatedAt = if_not_exists(CreatedAt, :c), UpdatedAt = :u ADD AdditionalFields :af""",
            ExpressionAttributeValues={
                ":ct": self.content_type.get_name(),
                ":cr": self.content_ref,
                ":crt": self.content_ref_type.value,
                ":af": self.additional_fields
                if self.additional_fields
                else {self.ADDITIONAL_FIELDS_PLACE_HOLDER},
                ":s": [s.isoformat() for s in self.submission_times],
                ":c": self.created_at.isoformat(),
                ":u": self.updated_at.isoformat(),
                ":empty_list": [],
            },
        )

    def write_to_table_if_not_found(self, table: Table) -> bool:
        """
        Write operations for this object need to be special cased (to avoid overwritting)
        Therefore we do not implement `to_dynamodb_item` however basically the body of that
        method is used here

        Returns false if a content object with that Id is already present
        and does not write to table. True is write was successful.
        """
        try:
            table.put_item(
                Item={
                    "PK": self.get_dynamodb_content_key(self.content_id),
                    "SK": self.get_dynamodb_content_type_key(),
                    "ContentType": self.content_type.get_name(),
                    "ContentRef": self.content_ref,
                    "ContentRefType": self.content_ref_type.value,
                    "AdditionalFields": self.additional_fields
                    if self.additional_fields
                    else {self.ADDITIONAL_FIELDS_PLACE_HOLDER},
                    "SubmissionTimes": [s.isoformat() for s in self.submission_times],
                    "CreatedAt": self.created_at.isoformat(),
                    "UpdatedAt": self.updated_at.isoformat(),
                },
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

    @classmethod
    def get_from_content_id(
        cls, table: Table, content_id: str, signal_type_mapping: HMASignalTypeMapping
    ) -> t.Optional["ContentObject"]:
        if not content_id:
            return None
        item = table.get_item(
            Key={
                "PK": cls.get_dynamodb_content_key(content_id),
                "SK": cls.get_dynamodb_content_type_key(),
            }
        ).get("Item", None)
        if item:
            return cls._result_item_to_object(item, signal_type_mapping)
        return None

    @classmethod
    def _result_item_to_object(
        cls, item: t.Dict, signal_type_mapping: HMASignalTypeMapping
    ) -> "ContentObject":
        content_ref_type = ContentRefType(item["ContentRefType"])
        content_type = signal_type_mapping.get_content_type_enforce(item["ContentType"])
        # This value is added in the case that no additional fields
        # were provided and can be safely discarded.
        item["AdditionalFields"].discard(cls.ADDITIONAL_FIELDS_PLACE_HOLDER)
        return ContentObject(
            content_id=cls.remove_content_key_prefix(
                item["PK"],
            ),
            content_type=content_type,
            content_ref=item["ContentRef"],
            content_ref_type=content_ref_type,
            additional_fields=item["AdditionalFields"],
            # Notes careful not using this version to write back to the table...
            # Will dup previous submissions...
            submission_times=[
                datetime.datetime.fromisoformat(s) for s in item["SubmissionTimes"]
            ],
            created_at=datetime.datetime.fromisoformat(item["CreatedAt"]),
            updated_at=datetime.datetime.fromisoformat(item["UpdatedAt"]),
        )
