# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle
import boto3

from enum import Enum
from dataclasses import dataclass, asdict, field
from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr, Key, Or
from botocore.exceptions import ClientError
import typing as t

from threatexchange.content_type.photo import PhotoContent

from hmalib.lambdas.api.middleware import jsoninator, JSONifiable, DictParseable
from hmalib.models import PipelineHashRecord
from hmalib.common.content_models import (
    ContentObject,
    ActionEvent,
    ContentRefType,
    ContentType,
)
from hmalib.common.content_sources import S3BucketContentSource
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
    action_events: t.List[ActionEvent] = field(default_factory=list)

    def to_json(self) -> t.Dict:
        return {"action_history": [record.to_json() for record in self.action_events]}


def get_content_api(
    dynamodb_table: Table, image_bucket: str, image_prefix: str
) -> bottle.Bottle:
    """
    A Closure that includes all dependencies that MUST be provided by the root
    API that this API plugs into. Declare dependencies here, but initialize in
    the root API alone.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/content/'
    content_api = bottle.Bottle()

    @content_api.get("/", apply=[jsoninator])
    def content() -> t.Optional[ContentObject]:
        """
        Content object for a given ID see
        hmalib/commom/content_models.ContentObject for specific fields

        TODO: Change the data model so that it does not require content_type,
        uniqueness and references should be maintainable without requiring
        content_type.
        """
        content_id = bottle.request.query.content_id or None
        content_type = bottle.request.query.content_type

        if content_id and content_type:
            return ContentObject.get_from_content_id(
                dynamodb_table, f"{content_id}", content_type=content_type
            )
        return None

    @content_api.get("/action-history/", apply=[jsoninator])
    def action_history() -> ActionHistoryResponse:
        """
        List of action event records for a given ID
        see hmalib/common/content_models.ActionEvent for specific fields
        """
        if content_id := bottle.request.query.content_id or None:
            return ActionHistoryResponse(
                ActionEvent.get_from_content_id(dynamodb_table, f"{content_id}")
            )
        return ActionHistoryResponse()

    @content_api.get("/hash/", apply=[jsoninator])
    def hashes() -> t.Optional[HashResultResponse]:
        """
        hash details for a given ID:
        """
        content_id = bottle.request.query.content_id or None
        if not content_id:
            return None

        # FIXME: Presently, hash API can only support one hash per content_id
        record = PipelineHashRecord.get_from_content_id(
            dynamodb_table, f"{content_id}"
        )[0]
        if not record:
            return None

        return HashResultResponse(
            content_id=record.content_id,
            content_hash=record.content_hash,
            updated_at=record.updated_at.isoformat(),
        )

    @content_api.get("/image/")
    def image():
        """
        return the bytes of an image in the "image_folder_key" based on content_id
        TODO update return url to request directly from s3?
        """
        content_id = bottle.request.query.content_id or None

        if not content_id:
            return bottle.abort(400, "content_id must be provided")

        content_object: ContentObject = ContentObject.get_from_content_id(
            table=dynamodb_table, content_id=content_id, content_type=PhotoContent
        )

        if not content_object:
            return bottle.abort(404, "content_id does not exist.")
        content_object = t.cast(ContentObject, content_object)

        if content_object.content_ref_type == ContentRefType.DEFAULT_S3_BUCKET:
            bytes_: bytes = S3BucketContentSource(
                image_bucket, image_prefix
            ).get_image_bytes(content_id)
            bottle.response.set_header("Content-type", "image/jpeg")
            return bytes_
        elif content_object.content_ref_type == ContentRefType.URL:
            return bottle.redirect(content_object.content_ref)

    return content_api
