# Copyright (c) Meta Platforms, Inc. and affiliates.

from threatexchange import signal_type
from hmalib.common.mappings import HMASignalTypeMapping
from hmalib.lambdas.api.submit import create_presigned_url
import bottle
import boto3
from datetime import datetime
from dataclasses import dataclass, asdict, field
from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr, Key, Or
from botocore.exceptions import ClientError
import typing as t

from threatexchange.signal_type.signal_base import SignalType
from threatexchange.content_type.content_base import ContentType

from hmalib.lambdas.api.middleware import (
    jsoninator,
    JSONifiable,
    DictParseable,
    SubApp,
)
from hmalib.common.models.pipeline import MatchRecord, PipelineHashRecord
from hmalib.common.models.content import (
    ContentObject,
    ActionEvent,
    ContentRefType,
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
class ContentPreviewResponse(JSONifiable):
    preview_url: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class ContentPipelineProgress(JSONifiable):
    """
    Encompasses optional results for all stages of the pipeline. Includes
    results from any of those stages and the time those stages were updated.
    """

    content_id: str
    content_type: t.Type[ContentType]
    content_preview_url: str

    # Stage update times
    submitted_at: t.Optional[datetime]
    hashed_at: t.Optional[datetime] = None
    matched_at: t.Optional[datetime] = None
    action_evaluated_at: t.Optional[datetime] = None
    action_performed_at: t.Optional[datetime] = None

    # Stage update results
    submission_additional_fields: t.List[str] = field(default_factory=list)

    # map from signal_type string => hash value
    hash_results: t.Dict[str, str] = field(default_factory=dict)

    # map from signal_id => set[classification_strings]
    match_results: t.Dict[str, t.List[str]] = field(default_factory=dict)

    # list of action names that must be performed
    action_evaluation_results: t.List[str] = field(default_factory=list)

    # list of action names that have been performed.
    action_perform_results: t.List[str] = field(default_factory=list)

    def to_json(self) -> t.Dict:
        result = asdict(self)
        result.update(
            content_type=self.content_type.get_name(),
            submitted_at=self.submitted_at and self.submitted_at.isoformat(),
            hashed_at=self.hashed_at and self.hashed_at.isoformat(),
            matched_at=self.matched_at and self.matched_at.isoformat(),
            action_evaluated_at=self.action_evaluated_at
            and self.action_evaluated_at.isoformat(),
            action_performed_at=self.action_performed_at
            and self.action_performed_at.isoformat(),
        )
        return result


@dataclass
class ActionHistoryResponse(JSONifiable):
    action_events: t.List[ActionEvent] = field(default_factory=list)

    def to_json(self) -> t.Dict:
        return {"action_history": [record.to_json() for record in self.action_events]}


def get_content_api(
    dynamodb_table: Table,
    image_bucket: str,
    image_prefix: str,
    signal_type_mapping: HMASignalTypeMapping,
) -> bottle.Bottle:
    """
    A Closure that includes all dependencies that MUST be provided by the root
    API that this API plugs into. Declare dependencies here, but initialize in
    the root API alone.
    """

    def get_preview_url(content_id, content_object) -> str:
        """
        Given a content_id and a content_object, returns a URL you can use to
        preview it.
        """
        content_object = t.cast(ContentObject, content_object)
        preview_url = ""
        if content_object.content_ref_type == ContentRefType.DEFAULT_S3_BUCKET:
            source = S3BucketContentSource(image_bucket, image_prefix)

            preview_url = create_presigned_url(
                image_bucket, source.get_s3_key(content_id), None, 3600, "get_object"
            )
        elif content_object.content_ref_type == ContentRefType.URL:
            preview_url = content_object.content_ref
        if not preview_url:
            return bottle.abort(400, "preview_url not found.")
        return preview_url

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/content/'
    content_api = SubApp()

    @content_api.get("/", apply=[jsoninator])
    def content() -> t.Optional[ContentObject]:
        """
        Return content object for given ID.
        """
        content_id = bottle.request.query.content_id or None

        if content_id:
            return ContentObject.get_from_content_id(
                dynamodb_table, content_id, signal_type_mapping
            )
        return None

    @content_api.get("/pipeline-progress/", apply=[jsoninator])
    def pipeline_progress() -> ContentPipelineProgress:
        """
        WARNING: UNOPTIMIZED. DO NOT CALL FROM AUTOMATED SYSTEMS.

        Build a history of the stages that this piece of content has gone
        through and what their results were. Do not call this from anything but
        a UI. This is not optimized for performance.
        """
        content_id = bottle.request.query.content_id or None

        if not content_id:
            return bottle.abort(400, "content_id must be provided.")
        content_id = t.cast(str, content_id)

        content_object = ContentObject.get_from_content_id(
            dynamodb_table, content_id, signal_type_mapping
        )
        if not content_object:
            return bottle.abort(400, f"Content with id '{content_id}' not found.")
        content_object = t.cast(ContentObject, content_object)

        preview_url = get_preview_url(content_id, content_object)

        # The result object will be gradually built up as records are retrieved.
        result = ContentPipelineProgress(
            content_id=content_id,
            content_type=content_object.content_type,
            content_preview_url=preview_url,
            submitted_at=content_object.updated_at,
            submission_additional_fields=list(content_object.additional_fields),
        )

        hash_records = PipelineHashRecord.get_from_content_id(
            dynamodb_table, content_id, signal_type_mapping
        )
        if len(hash_records) != 0:
            result.hashed_at = max(hash_records, key=lambda r: r.updated_at).updated_at
            for hash_record in hash_records:
                # Assume that each signal type has a single hash
                if hash_record.signal_type.get_name() in result.hash_results:
                    return bottle.abort(
                        500,
                        f"Content with id '{content_id}' has multiple hash records for signal-type: '{hash_record.signal_type.get_name()}'.",
                    )

                result.hash_results[
                    hash_record.signal_type.get_name()
                ] = hash_record.content_hash

        match_records = MatchRecord.get_from_content_id(
            dynamodb_table, content_id, signal_type_mapping
        )
        if len(match_records) != 0:
            result.matched_at = max(
                match_records, key=lambda r: r.updated_at
            ).updated_at

            # TODO #751 Until we resolve type agnostic storage of signal data,
            # we can't populate match details.
            # actually populate result.match_results.

        # TODO: ActionEvaluation does not yet leave a trail. Either record
        # action evaluation or remove the evaluation stage from the
        # pipeline-progress indicator.

        action_records = ActionEvent.get_from_content_id(dynamodb_table, content_id)
        if len(action_records) != 0:
            result.action_performed_at = max(
                action_records, key=lambda r: r.performed_at
            ).performed_at
            result.action_perform_results = [r.action_label for r in action_records]

        return result

    @content_api.get("/action-history/", apply=[jsoninator])
    def action_history() -> ActionHistoryResponse:
        """
        Return list of action event records for a given ID.
        """
        if content_id := bottle.request.query.content_id or None:
            return ActionHistoryResponse(
                ActionEvent.get_from_content_id(dynamodb_table, f"{content_id}")
            )
        return ActionHistoryResponse()

    @content_api.get("/hash/", apply=[jsoninator])
    def hashes() -> t.Optional[HashResultResponse]:
        """
        Return the hash details for a given ID.
        """
        content_id = bottle.request.query.content_id or None
        if not content_id:
            return None

        # FIXME: Presently, hash API can only support one hash per content_id
        record = PipelineHashRecord.get_from_content_id(
            dynamodb_table, f"{content_id}", signal_type_mapping
        )[0]
        if not record:
            return None

        return HashResultResponse(
            content_id=record.content_id,
            content_hash=record.content_hash,
            updated_at=record.updated_at.isoformat(),
        )

    @content_api.get("/preview-url/", apply=[jsoninator])
    def image():
        """
        Return the a URL to submitted media for a given ID.
        If URL was submitted is it returned
        else creates a signed URL for s3 uploads.
        Also works for videos.
        """
        content_id = bottle.request.query.content_id or None

        if not content_id:
            return bottle.abort(400, "content_id must be provided.")

        content_object: ContentObject = ContentObject.get_from_content_id(
            table=dynamodb_table, content_id=content_id
        )

        if not content_object:
            return bottle.abort(404, "content_id does not exist.")
        preview_url = get_preview_url(content_id, content_object)

        return ContentPreviewResponse(preview_url)

    return content_api
