# Copyright (c) Meta Platforms, Inc. and affiliates.

from dataclasses import dataclass
from decimal import Decimal
import typing as t

from mypy_boto3_dynamodb.service_resource import Table
from botocore.exceptions import ClientError


class DynamoDBItem:

    CONTENT_KEY_PREFIX = "c#"
    SIGNAL_KEY_PREFIX = "s#"
    TYPE_PREFIX = "type#"

    SET_PLACEHOLDER_VALUE = "SET_PLACEHOLDER_VALUE"

    def write_to_table(self, table: Table):
        table.put_item(Item=self.to_dynamodb_item())

    def write_to_table_if_not_found(self, table: Table) -> bool:
        """
        Write record to DDB if the PK/SK combination does not exist.

        Returns:
        * True when record was written (did not exist)
        * False when record could not be written (PK/SK combo existed)
        """
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

    @classmethod
    def set_to_dynamodb_attribute(cls, value: t.Set) -> t.Set:
        if not value or len(value) == 0:
            return set([cls.SET_PLACEHOLDER_VALUE])

        return value

    @classmethod
    def dynamodb_attribute_to_set(cls, value: t.Set) -> t.Set:
        if len(value) == 1:
            elem = value.pop()
            if elem == cls.SET_PLACEHOLDER_VALUE:
                return set()
            else:
                value.add(elem)

        return value


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


T = t.TypeVar("T")


@dataclass
class PaginatedResponse(t.Generic[T]):
    """
    A generic paginated resopnse container for list of items queried/scanned
    from dynamodb.
    """

    last_evaluated_key: DynamoDBCursorKey
    items: t.List[T]

    def has_next_page(self):
        """
        If query does not return last_evaluated_key, there are no more results
        to return.

        https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html
        """
        return self.last_evaluated_key != None
