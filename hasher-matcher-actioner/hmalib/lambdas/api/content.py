# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle
import boto3
import base64
import requests
import datetime

from enum import Enum
from dataclasses import dataclass, asdict
from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr, Key, Or
from botocore.exceptions import ClientError
import typing as t

from hmalib.lambdas.api.middleware import jsoninator, JSONifiable, DictParseable
from hmalib.models import PipelinePDQHashRecord
from hmalib.common.content_models import ContentObject, ActionEvent
from hmalib.common.logging import get_logger

logger = get_logger(__name__)
s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")


@dataclass
class HashResultResponse(JSONifiable):
    content_id: str
    content_hash: str
    updated_at: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class ActionHistoryResponse(JSONifiable):
    action_records: t.List[ActionEvent]

    def to_json(self) -> t.Dict:
        return {"action_history": [record.to_json() for record in self.action_records]}


def get_content_api(
    dynamodb_table: Table, image_bucket_key: str, image_folder_key: str
) -> bottle.Bottle:
    """
    A Closure that includes all dependencies that MUST be provided by the root
    API that this API plugs into. Declare dependencies here, but initialize in
    the root API alone.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/content/'
    content_api = bottle.Bottle()
    image_folder_key_len = len(image_bucket_key)

    @content_api.get("/<key>", apply=[jsoninator])
    def content(key=None) -> t.Optional[ContentObject]:
        """
        Content object for a given ID
        see hmalib/commom/content_models.ContentObject for specific fields
        """
        return ContentObject.get_from_content_id(dynamodb_table, key)

    @content_api.get("/action-history/<key>", apply=[jsoninator])
    def action_history(key=None) -> ActionHistoryResponse:
        """
        List of action event records for a given ID
        see hmalib/common/content_models.ActionEvent for specific fields
        """
        return ActionHistoryResponse(
            ActionEvent.get_from_content_id(dynamodb_table, key)
        )

    @content_api.get("/hash/<key>", apply=[jsoninator])
    def hashes(key=None) -> t.Optional[HashResultResponse]:
        """
        hash details for a given ID:
        """
        if not key:
            return None
        record = PipelinePDQHashRecord.get_from_content_id(
            dynamodb_table, f"{image_folder_key}{key}"
        )
        if not record:
            return None
        return HashResultResponse(
            content_id=record.content_id[len(image_folder_key) :],
            content_hash=record.content_hash,
            updated_at=record.updated_at.isoformat(),
        )

    @content_api.get("/image/<key>")
    def image(key=None):
        """
        return the bytes of an image in the "image_folder_key" based on key
        TODO update return url to request directly from s3?
        """
        logger.info(key)
        if not key:
            return
        # TODO a whole bunch of validation and error checking...
        bytes_: bytes = s3_client.get_object(
            Bucket=image_bucket_key, Key=f"{image_folder_key}{key}"
        )["Body"].read()
        # TODO make the content type dynamic
        bottle.response.set_header("Content-type", "image/jpeg")
        return bytes_

    return content_api
