# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import functools
import bottle
import boto3
import base64
import json
import datetime
import dataclasses

from enum import Enum
from dataclasses import dataclass, asdict
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_sqs import SQSClient
from botocore.exceptions import ClientError
import typing as t

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.meta import get_content_type_for_name
from threatexchange.signal_type.pdq import PdqSignal


from hmalib.lambdas.api.middleware import jsoninator, JSONifiable, DictParseable
from hmalib.common.content_sources import S3BucketContentSource
from hmalib.common.content_models import ContentObject, ContentRefType
from hmalib.common.logging import get_logger
from hmalib.common.message_models import URLSubmissionMessage
from hmalib.models import PipelineHashRecord

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
class SubmitRequestBodyBase(DictParseable):
    content_id: str
    content_type: t.Type[ContentType]
    additional_fields: t.Optional[t.List]
    force_resubmit: bool = False

    def get_content_ref_details(self) -> t.Tuple[str, ContentRefType]:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, d):
        base = cls(**{f.name: d.get(f.name, None) for f in dataclasses.fields(cls)})
        base.content_type = get_content_type_for_name(base.content_type)
        return base


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
    signal_type: str = ""  # SignalType.getname() values
    content_url: str = ""

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
) -> bottle.Bottle:
    """
    A Closure that includes all dependencies that MUST be provided by the root
    API that this API plugs into. Declare dependencies here, but initialize in
    the root API alone.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/submit/'
    submit_api = bottle.Bottle()
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

    @submit_api.post("/", apply=[jsoninator])
    def submit() -> SubmitError:
        """
        Root for the general submission of content to the system.
        Currently just provides 400 error code (todo delete, leaving now for debug help)
        """

        logger.info(f"Submit attempted on root submit endpoint.")

        bottle.response.status = 400
        return SubmitError(
            content_id="",
            message="Submission not supported from just /submit/.",
        )

    @submit_api.post("/url/", apply=[jsoninator(SubmitContentViaURLRequestBody)])
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

    @submit_api.post("/bytes/", apply=[jsoninator(SubmitContentBytesRequestBody)])
    def submit_bytes(
        request: SubmitContentBytesRequestBody,
    ) -> t.Union[SubmitResponse, SubmitError]:
        """
        Direct transfer of bits to system's s3 bucket
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
        "/put-url/", apply=[jsoninator(SubmitContentViaPutURLUploadRequestBody)]
    )
    def submit_put_url(
        request: SubmitContentViaPutURLUploadRequestBody,
    ) -> t.Union[SubmitViaUploadUrlResponse, SubmitError]:
        """
        Submission of content to the system's s3 bucket by providing a put url to client
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

    @submit_api.post("/hash/", apply=[jsoninator(SubmitContentHashRequestBody)])
    def submit_hash(
        request: SubmitContentHashRequestBody,
    ) -> t.Union[SubmitResponse, SubmitError]:
        """
        Endpoint to submit a hash of a piece of content
        """

        # Record content object (even though we don't store anything just like with url)
        if not _record_content_submission_from_request(request):
            return _content_exist_error(request.content_id)

        # Record hash
        # todo add MD5 support and branch based on request.hash_type
        #   note: quality of PDQ hashes should part of `signal_specific_attributes` after #749/related is merged
        hash_record = PipelineHashRecord(
            content_id=request.content_id,
            signal_type=PdqSignal,
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
