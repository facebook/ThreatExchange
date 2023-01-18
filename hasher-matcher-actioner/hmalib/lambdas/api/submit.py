# Copyright (c) Meta Platforms, Inc. and affiliates.

import functools
import bottle
import boto3
import base64
import json
import datetime
import dataclasses

from uuid import uuid4
from enum import Enum
from dataclasses import dataclass, asdict
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_sqs import SQSClient
from botocore.exceptions import ClientError
import typing as t

from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import SignalType


from hmalib.lambdas.api.middleware import (
    DictParseableWithSignalTypeMapping,
    jsoninator,
    JSONifiable,
    DictParseable,
    SubApp,
)
from hmalib.common.content_sources import S3BucketContentSource
from hmalib.common.models.content import ContentObject, ContentRefType
from hmalib.common.logging import get_logger
from hmalib.common.mappings import HMASignalTypeMapping
from hmalib.common.messages.submit import URLSubmissionMessage
from hmalib.common.models.pipeline import PipelineHashRecord

logger = get_logger(__name__)


@functools.lru_cache(maxsize=None)
def _get_sqs_client() -> SQSClient:
    return boto3.client("sqs")


def create_presigned_put_url(bucket_name, key, file_type, expiration=3600):
    return create_presigned_url(bucket_name, key, file_type, expiration, "put_object")


def create_presigned_url(bucket_name, key, file_type, expiration, client_method):
    """
    Generate a presigned URL to share an S3 object
    """

    s3_client = boto3.client("s3")
    params = {
        "Bucket": bucket_name,
        "Key": key,
    }
    if file_type:
        params["ContentType"] = file_type

    try:
        response = s3_client.generate_presigned_url(
            client_method,
            Params=params,
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logger.error(e)
        return None

    return response


# Request Objects
@dataclass
class SubmitRequestBodyBase(DictParseableWithSignalTypeMapping):
    content_id: str
    content_type: t.Type[ContentType]
    additional_fields: t.Optional[t.List]
    force_resubmit: bool = False

    def get_content_ref_details(self) -> t.Tuple[str, ContentRefType]:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, d, signal_type_mapping: HMASignalTypeMapping):
        base = cls(**{f.name: d.get(f.name, None) for f in dataclasses.fields(cls)})
        base.content_type = signal_type_mapping.get_content_type_enforce(
            base.content_type  # type:ignore
        )
        return base


@dataclass
class SubmitContents3ObjectRequestBody(SubmitRequestBodyBase):
    bucket_name: str = ""
    object_key: str = ""


@dataclass
class SubmitContentViaURLRequestBody(SubmitRequestBodyBase):
    content_url: str = ""

    def get_content_ref_details(self) -> t.Tuple[str, ContentRefType]:
        return (self.content_url, ContentRefType.URL)


@dataclass
class SubmitContentBytesRequestBody(SubmitRequestBodyBase):
    content_bytes: bytes = b""

    def get_content_ref_details(self) -> t.Tuple[str, ContentRefType]:
        return (self.content_id, ContentRefType.DEFAULT_S3_BUCKET)


@dataclass
class SubmitContentHashRequestBody(SubmitRequestBodyBase):
    signal_value: str = ""
    signal_type: t.Union[t.Type[SignalType], str] = ""  # SignalType.getname() values
    content_url: str = ""

    @classmethod
    def from_dict(cls, d, signal_type_mapping: HMASignalTypeMapping):
        base = super().from_dict(d, signal_type_mapping)
        base.signal_type = signal_type_mapping.get_signal_type_enforce(base.signal_type)
        return base

    def get_content_ref_details(self) -> t.Tuple[str, ContentRefType]:
        if self.content_url:
            return (self.content_url, ContentRefType.URL)
        return ("", ContentRefType.NONE)


@dataclass
class SubmitContentViaPutURLUploadRequestBody(SubmitRequestBodyBase):
    file_type: str = ""

    def get_content_ref_details(self) -> t.Tuple[str, ContentRefType]:
        # Treat this as an S3 submission because
        # we expect the client to upload it there directly
        return (self.content_id, ContentRefType.DEFAULT_S3_BUCKET)


# Response Objects
@dataclass
class SubmitResponse(JSONifiable):
    content_id: str
    submit_successful: bool

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class SubmitViaUploadUrlResponse(JSONifiable):
    content_id: str
    file_type: str
    presigned_url: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class SubmitError(JSONifiable):
    """
    Warning: by default this will still return 200
    you need to update bottle.response.status
    if you want a specific return code.
    ToDo update middleware.py to handle this.
    """

    content_id: str
    message: str

    def to_json(self) -> t.Dict:
        return asdict(self)


def submit_content_request_from_s3_object(
    dynamodb_table: Table,
    submissions_queue_url: str,
    bucket: str,
    key: str,
    content_id: str = "",
    content_type: ContentType = PhotoContent,
    additional_fields: t.Set = set(),
    force_resubmit: bool = False,
):
    """
    Converts s3 event into a ContentObject and url_submission_message using helpers
    from submit.py

    For partner bucket uploads, the content IDs are unique and (somewhat) readable but
    not reversable
      * uniqueness is provided by uuid4 which has a collision rate of 2^-36
      * readability is provided by including part of the key in the content id
      * modifications to the key mean that the original content bucket and key are
        not derivable from the content ID alone

    The original content (bucket and key) is stored in the reference url which is passed
    to the webhook via additional_fields

    Q: Why not include full key and bucket in content_id?
    A: Bucket keys often have "/" which dont work well with ContentDetails UI page
    """

    readable_key = key.split("/")[-1].replace("?", ".").replace("&", ".")
    if not content_id:
        content_id = f"{uuid4()}-{readable_key}"

    presigned_url = create_presigned_url(bucket, key, None, 3600, "get_object")
    reference_url = f"https://{bucket}.s3.amazonaws.com/{key}"
    additional_fields.update(
        {
            f"s3_reference_url:{reference_url}",
            f"bucket_name:{bucket}",
            f"object_key:{key}",
        }
    )

    record_content_submission(
        dynamodb_table,
        content_id,
        content_type,
        content_ref=presigned_url,
        content_ref_type=ContentRefType.URL,
        additional_fields=additional_fields,
    )
    send_submission_to_url_queue(
        dynamodb_table, submissions_queue_url, content_id, content_type, presigned_url
    )


def record_content_submission(
    dynamodb_table: Table,
    content_id: str,
    content_type: ContentType,
    content_ref: str,
    content_ref_type: ContentRefType,
    additional_fields: t.Set = set(),
    force_resubmit: bool = False,
) -> bool:
    """
    Write a content object that is submitted to the dynamodb_table.

    Note: this method does not store the data of the content itself
    If we want to store the media itself that is done either:
    - by a client using a presign url we give them
    - direct s3 put call in the case of raw bytes
    - not at all in the case of CDN-URL submission
        - (WIP: possibly done after a match is found)

    This function is also called directly by api_root when handling s3 uploads to partner
    banks. If editing, ensure the logic in api_root.process_s3_event is still correct

    Return True with recording was successful.
    """

    submit_time = datetime.datetime.now()
    content_obj = ContentObject(
        content_id=content_id,
        content_type=content_type,
        content_ref=content_ref,
        content_ref_type=content_ref_type,
        additional_fields=additional_fields,
        submission_times=[submit_time],  # Note: custom write_to_table impl appends.
        created_at=submit_time,
        updated_at=submit_time,
    )

    if force_resubmit:
        # Allow an overwrite or resubmission of content objects
        content_obj.write_to_table(dynamodb_table)
        return True

    return content_obj.write_to_table_if_not_found(dynamodb_table)


def send_submission_to_url_queue(
    dynamodb_table: Table,
    submissions_queue_url: str,
    content_id: str,
    content_type: ContentType,
    url: str,
):
    """
    Send a submitted url of content to the hasher. This does not store a copy of the content in s3

    This function is also called directly by api_root when handling s3 uploads to partner
    banks. If editing, ensure the logic in api_root.process_s3_event is still correct
    """

    url_submission_message = URLSubmissionMessage(
        content_type=content_type, content_id=content_id, url=t.cast(str, url)
    )
    _get_sqs_client().send_message(
        QueueUrl=submissions_queue_url,
        MessageBody=json.dumps(url_submission_message.to_sqs_message()),
    )


def get_submit_api(
    dynamodb_table: Table,
    image_bucket: str,
    image_prefix: str,
    submissions_queue_url: str,
    hash_queue_url: str,
    signal_type_mapping: HMASignalTypeMapping,
) -> bottle.Bottle:
    """
    A Closure that includes all dependencies that MUST be provided by the root
    API that this API plugs into. Declare dependencies here, but initialize in
    the root API alone.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/submit/'
    submit_api = SubApp()
    s3_bucket_image_source = S3BucketContentSource(image_bucket, image_prefix)

    def _content_exist_error(content_id: str):
        return bottle.abort(
            400,
            f"Content with id '{content_id}' already exists if you want to resubmit `force_resubmit=True` must be included in payload.",
        )

    def _record_content_submission_from_request(
        request: SubmitRequestBodyBase,
    ) -> bool:
        """
        Given a request object submission record the content object to the table passed to
        the API using 'record_content_submission'
        Note: this method does not store the content media itself.
        """

        content_ref, content_ref_type = request.get_content_ref_details()

        return record_content_submission(
            dynamodb_table,
            content_id=request.content_id,
            content_type=request.content_type,
            content_ref=content_ref,
            content_ref_type=content_ref_type,
            additional_fields=set(request.additional_fields)
            if request.additional_fields
            else set(),
            force_resubmit=request.force_resubmit,
        )

    @submit_api.post(
        "/s3/",
        apply=[
            jsoninator(
                SubmitContents3ObjectRequestBody,
                signal_type_mapping=signal_type_mapping,
            )
        ],
    )
    def submit_s3(
        request: SubmitContents3ObjectRequestBody,
    ) -> t.Union[SubmitResponse, SubmitError]:
        """
        Submission of a s3 object of a piece of content.
        """
        submit_content_request_from_s3_object(
            dynamodb_table,
            submissions_queue_url=submissions_queue_url,
            bucket=request.bucket_name,
            key=request.object_key,
            content_id=request.content_id,
            content_type=request.content_type,
            additional_fields=set(request.additional_fields)
            if request.additional_fields
            else set(),
            force_resubmit=request.force_resubmit,
        )

        return SubmitResponse(content_id=request.content_id, submit_successful=True)

    @submit_api.post(
        "/url/",
        apply=[
            jsoninator(
                SubmitContentViaURLRequestBody,
                signal_type_mapping=signal_type_mapping,
            )
        ],
    )
    def submit_url(
        request: SubmitContentViaURLRequestBody,
    ) -> t.Union[SubmitResponse, SubmitError]:
        """
        Submission via a url to content. This does not store a copy of the content in s3
        """
        if not _record_content_submission_from_request(request):
            return _content_exist_error(request.content_id)

        send_submission_to_url_queue(
            dynamodb_table,
            submissions_queue_url,
            request.content_id,
            request.content_type,
            request.content_url,
        )

        return SubmitResponse(content_id=request.content_id, submit_successful=True)

    @submit_api.post(
        "/bytes/",
        apply=[
            jsoninator(
                SubmitContentBytesRequestBody,
                signal_type_mapping=signal_type_mapping,
            )
        ],
    )
    def submit_bytes(
        request: SubmitContentBytesRequestBody,
    ) -> t.Union[SubmitResponse, SubmitError]:
        """
        Submit of media to HMA via a direct transfer of bytes to the system's s3 bucket.
        """
        content_id = request.content_id
        file_contents = base64.b64decode(request.content_bytes)

        # We want to record the submission before triggering and processing on
        # the content itself therefore we write to dynamodb before s3
        if not _record_content_submission_from_request(request):
            return _content_exist_error(request.content_id)

        s3_bucket_image_source.put_image_bytes(content_id, file_contents)

        return SubmitResponse(content_id=request.content_id, submit_successful=True)

    @submit_api.post(
        "/put-url/",
        apply=[
            jsoninator(
                SubmitContentViaPutURLUploadRequestBody,
                signal_type_mapping=signal_type_mapping,
            )
        ],
    )
    def submit_put_url(
        request: SubmitContentViaPutURLUploadRequestBody,
        signal_type_mapping=signal_type_mapping,
    ) -> t.Union[SubmitViaUploadUrlResponse, SubmitError]:
        """
        Submission of content to HMA in two steps
        1st the creation to a content record and put url based on request body
        2nd Upload to the system's s3 bucket by said put url returned by this method
        """
        presigned_url = create_presigned_put_url(
            bucket_name=image_bucket,
            key=s3_bucket_image_source.get_s3_key(request.content_id),
            file_type=request.file_type,
        )

        if presigned_url:
            if not _record_content_submission_from_request(request):
                return _content_exist_error(request.content_id)

            return SubmitViaUploadUrlResponse(
                content_id=request.content_id,
                file_type=str(request.file_type),
                presigned_url=presigned_url,
            )

        bottle.response.status = 400
        return SubmitError(
            content_id=request.content_id,
            message="Failed to generate upload url",
        )

    @submit_api.post(
        "/hash/",
        apply=[
            jsoninator(
                SubmitContentHashRequestBody,
                signal_type_mapping=signal_type_mapping,
            )
        ],
    )
    def submit_hash(
        request: SubmitContentHashRequestBody,
    ) -> t.Union[SubmitResponse, SubmitError]:
        """
        Submission of a hash from a piece of content.
        Functions the same as other submission endpoint but skips
        the hasher and media storage.
        """

        # Record content object (even though we don't store anything just like with url)
        if not _record_content_submission_from_request(request):
            return _content_exist_error(request.content_id)

        # Record hash
        #   ToDo expand submit hash API to include `signal_specific_attributes`
        hash_record = PipelineHashRecord(
            content_id=request.content_id,
            signal_type=t.cast(t.Type[SignalType], request.signal_type),
            content_hash=request.signal_value,
            updated_at=datetime.datetime.now(),
        )
        hash_record.write_to_table(dynamodb_table)

        # Send hash directly to matcher
        # todo this could maybe try and reuse the methods in UnifiedHasher in #749
        _get_sqs_client().send_message(
            QueueUrl=hash_queue_url,
            MessageBody=json.dumps(hash_record.to_sqs_message()),
        )

        return SubmitResponse(content_id=request.content_id, submit_successful=True)

    return submit_api
