# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import datetime
from enum import Enum
import typing as t

from dataclasses import dataclass, field
from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr, Key, And
from botocore.exceptions import ClientError

from hmalib.models import DynamoDBItem


@dataclass
class ContentObjectBase(DynamoDBItem):
    """
    TODO docstring
    """

    CONTENT_ID_PREFIX = "cid#"
    CONTENT_TYPE_PREFIX = "type#"

    content_id: str
    content_type: str
    content_ref: str
    content_ref_type: str
    submitted_fields: t.Optional[t.Dict]
    submissions: t.List
    created_on: datetime.datetime
    last_updated_on: datetime.datetime

    @staticmethod
    def get_dynamodb_ds_key(content_id: str) -> str:
        return f"{ContentObjectBase.CONTENT_ID_PREFIX}{content_id}"
