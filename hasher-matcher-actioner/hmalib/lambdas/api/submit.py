# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import functools
from hmalib.common.image_sources import S3BucketImageSource
import bottle
import boto3
import base64
import json
import datetime

from enum import Enum
from dataclasses import dataclass, asdict
from mypy_boto3_dynamodb.service_resource import Table
from botocore.exceptions import ClientError
import typing as t

from hmalib.lambdas.api.middleware import jsoninator, JSONifiable, DictParseable
from hmalib.common.content_models import ContentObject, ContentRefType, ContentType
from hmalib.common.logging import get_logger
from hmalib.common.message_models import URLImageSubmissionMessage

logger = get_logger(__name__)
s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")


@functools.lru_cache(maxsize=None)
def _get_sns_client():
    return boto3.client("sns")


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


@dataclass
class InitUploadResponse(JSONifiable):
    content_id: str
    file_type: str
    presigned_url: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class InitUploadRequestBody(DictParseable):
    content_id: str
    file_type: str

    @classmethod
    def from_dict(cls, d):
        return cls(d["content_id"], d["file_type"])


class SubmissionType(Enum):
    POST_URL_UPLOAD = "Upload"
    DIRECT_UPLOAD = "Direct Upload (~faster but only works for images < 3.5MB)"
    FROM_URL = "From URL"


@dataclass
class SubmitContentRequestBody(DictParseable):
    submission_type: str  # Enum SubmissionType names
    content_id: str
    content_type: str  # Only PHOTO supported. TODO: @schatten change to content_type enum
    content_bytes_url_or_file_type: t.Union[str, bytes]
    additional_fields: t.Optional[t.List]

    @classmethod
    def from_dict(cls, d):
        # ToDo Cleaner error handling
        return cls(
            d["submission_type"],
            d["content_id"],
            d["content_type"],
            d["content_bytes_url_or_file_type"],
            d["additional_fields"],
        )


@dataclass
class SubmitContentResponse(JSONifiable):
    content_id: str
    submit_successful: bool

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class SubmitContentError(JSONifiable):
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


def record_content_submission(dynamodb_table: Table, request: SubmitContentRequestBody):
    # TODO add a confirm overwrite path for this
    submit_time = datetime.datetime.now()
    if request.submission_type in (
        SubmissionType.FROM_URL,
        SubmissionType.FROM_URL.name,
    ):
        # ^ Someday we'll have type inference between enum and enum values,
        # until then, this is how it is.
        content_ref_type = ContentRefType.URL
        content_ref = t.cast(str, request.content_bytes_url_or_file_type)
    else:
        # defaults to DEFAULT_S3_BUCKET
        content_ref_type = ContentRefType.DEFAULT_S3_BUCKET
        content_ref = request.content_id

    ContentObject(
        content_id=request.content_id,
        content_type=ContentType(request.content_type or ContentType.PHOTO),
        content_ref=content_ref,
        content_ref_type=content_ref_type,
        additional_fields=set(request.additional_fields)
        if request.additional_fields
        else set(),
        submission_times=[submit_time],  # Note: custom write_to_table impl appends.
        created_at=submit_time,
        updated_at=submit_time,
    ).write_to_table(dynamodb_table)


def submit_from_url(
    request: SubmitContentRequestBody, dynamodb_table: Table, images_topic_arn: str
) -> SubmitContentResponse:
    """
    Submission via a url to content. This does not store a copy of the content in s3

    This function is also called directly by api_root when handling s3 uploads to partner
    banks. If editing, ensure the logic in api_root.process_s3_event is still correct
    """
    content_id = request.content_id
    url = request.content_bytes_url_or_file_type

    # Again, We want to record the submission before triggering and processing on
    # the content itself therefore we write to dynamo before s3
    record_content_submission(dynamodb_table, request)

    url_submission_message = URLImageSubmissionMessage(content_id, t.cast(str, url))
    _get_sns_client().publish(
        TopicArn=images_topic_arn,
        Message=json.dumps(url_submission_message.to_sqs_message()),
    )

    return SubmitContentResponse(content_id=request.content_id, submit_successful=True)


def get_submit_api(
    dynamodb_table: Table,
    image_bucket: str,
    image_prefix: str,
    images_topic_arn: str,
) -> bottle.Bottle:
    """
    A Closure that includes all dependencies that MUST be provided by the root
    API that this API plugs into. Declare dependencies here, but initialize in
    the root API alone.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/submit/'
    submit_api = bottle.Bottle()
    s3_bucket_image_source = S3BucketImageSource(image_bucket, image_prefix)

    # Set of helpers that could be split into there own submit endpoints depending on longterm design choices

    def direct_upload(
        request: SubmitContentRequestBody,
    ) -> t.Union[SubmitContentResponse, SubmitContentError]:
        """
        Direct transfer of bits to system's s3 bucket
        """
        content_id = request.content_id
        file_contents = base64.b64decode(request.content_bytes_url_or_file_type)

        # We want to record the submission before triggering and processing on
        # the content itself therefore we write to dynamo before s3
        record_content_submission(dynamodb_table, request)

        # TODO a whole bunch more validation and error checking...
        s3_bucket_image_source.put_image_bytes(content_id, file_contents)

        return SubmitContentResponse(
            content_id=request.content_id, submit_successful=True
        )

    def post_url_upload(
        request: SubmitContentRequestBody,
    ) -> t.Union[InitUploadResponse, SubmitContentError]:
        """
        Submission of content to the system's s3 bucket by providing a post url to client
        """
        presigned_url = create_presigned_put_url(
            bucket_name=image_bucket,
            key=s3_bucket_image_source.get_s3_key(request.content_id),
            file_type=request.content_bytes_url_or_file_type,
        )

        if presigned_url:
            record_content_submission(dynamodb_table, request)
            return InitUploadResponse(
                content_id=request.content_id,
                file_type=str(request.content_bytes_url_or_file_type),
                presigned_url=presigned_url,
            )

        bottle.response.status = 400
        return SubmitContentError(
            content_id=request.content_id,
            message="not yet supported",
        )

    def from_url(
        request: SubmitContentRequestBody,
    ) -> t.Union[SubmitContentResponse, SubmitContentError]:
        """
        Submission via a url to content. This does not store a copy of the content in s3
        """
        return submit_from_url(request, dynamodb_table, images_topic_arn)

    @submit_api.post("/", apply=[jsoninator(SubmitContentRequestBody)])
    def submit(
        request: SubmitContentRequestBody,
    ) -> t.Union[SubmitContentResponse, InitUploadResponse, SubmitContentError]:
        """
        Endpoint to allow for the general submission of content to the system
        """

        assert isinstance(request, SubmitContentRequestBody)
        logger.debug(f"Content Submit Request Received {request.content_id}")

        if request.submission_type == SubmissionType.DIRECT_UPLOAD.name:
            return direct_upload(request)
        elif request.submission_type == SubmissionType.POST_URL_UPLOAD.name:
            return post_url_upload(request)
        elif request.submission_type == SubmissionType.FROM_URL.name:
            return from_url(request)
        else:
            # Other possible submission types are not supported so just echo content_id for testing
            bottle.response.status = 422
            return SubmitContentError(
                content_id=request.content_id,
                message="submission_type not yet supported",
            )

    @submit_api.post("/init-upload/", apply=[jsoninator(InitUploadRequestBody)])
    def init_upload(
        request: InitUploadRequestBody,
    ) -> t.Union[InitUploadResponse, SubmitContentError]:
        """
        Endpoint to provide requester with presigned url to upload a photo
        """

        # TODO error checking on if key already exist etc.
        presigned_url = create_presigned_put_url(
            bucket_name=image_bucket,
            key=s3_bucket_image_source.get_s3_key(request.content_id),
            file_type=request.file_type,
        )
        if presigned_url:
            return InitUploadResponse(
                content_id=request.content_id,
                file_type=request.file_type,
                presigned_url=presigned_url,
            )

        bottle.response.status = 400
        return SubmitContentError(
            content_id=request.content_id,
            message="not yet supported",
        )

    return submit_api
