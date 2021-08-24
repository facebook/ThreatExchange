# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from decimal import Decimal
import typing as t

from mypy_boto3_dynamodb.service_resource import Table
from botocore.exceptions import ClientError


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


# DDB's internal LastEvaluatedKey and ExclusiveStartKey both follow this type.
# Naming Struggle: Is this a "real" cursor, dunno, but "DynamoDBKey" is too
# confusable. Needed to add something to distinguish. Using "Cursor" now.
DynamoDBCursorKey = t.NewType(
    "DynamoDBCursorKey",
    t.Dict[
        str,
        t.Union[
            bytes,
            bytearray,
            str,
            int,
            bool,
            Decimal,
            t.Set[int],
            t.Set[Decimal],
            t.Set[str],
            t.Set[bytes],
            t.Set[bytearray],
            t.List[t.Any],
            t.Dict[str, t.Any],
            None,
        ],
    ],
)
