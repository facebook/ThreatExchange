# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle
import boto3
import base64
import json

from dataclasses import dataclass, asdict
from mypy_boto3_dynamodb.service_resource import Table
import typing as t

from hmalib.lambdas.api.middleware import jsoninator, JSONifiable, DictParseable
from hmalib.common.logging import get_logger

logger = get_logger(__name__)
s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")


@dataclass
class SubmitContentRequestBody(DictParseable):
    submission_type: str  # TODO Enum
    content_id: str
    content_type: str  # TODO Enum
    content_ref: t.Union[str, bytes]
    metadata: t.Optional[t.List]

    @classmethod
    def from_dict(cls, d):
        # ToDo Cleaner error handling
        return cls(
            d["submission_type"],
            d["content_id"],
            d["content_type"],
            d["content_ref"],
            d["metadata"],
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
    Warning: by defualt this will still return 200
    you need to update bottle.response.status
    if you want a specific return code.
    ToDo update middleware.py to handle this.
    """

    content_id: str
    message: str

    def to_json(self) -> t.Dict:
        return asdict(self)


def get_submit_api(
    dynamodb_table: Table, image_bucket_key: str, image_folder_key: str
) -> bottle.Bottle:
    """
    A Closure that includes all dependencies that MUST be provided by the root
    API that this API plugs into. Declare dependencies here, but initialize in
    the root API alone.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/submit/'
    submit_api = bottle.Bottle()

    @submit_api.post("/", apply=[jsoninator(SubmitContentRequestBody)])
    def submit(
        request: SubmitContentRequestBody,
    ) -> t.Union[SubmitContentResponse, SubmitContentError]:
        """
        Endpoint to allow for the general submission of content to the system
        """

        assert isinstance(request, SubmitContentRequestBody)
        logger.debug(f"Content Submit Request Received {request.content_id}")

        if request.submission_type == "UPLOAD":
            fileName = request.content_id
            fileContents = base64.b64decode(request.content_ref)
            # TODO a whole bunch more validation and error checking...
            s3_client.put_object(
                Body=fileContents,
                Bucket=image_bucket_key,
                Key=f"{image_folder_key}{fileName}",
            )

            return SubmitContentResponse(
                content_id=request.content_id, submit_successful=True
            )

        # Other possible submission types are not supported so just echo content_id for testing
        bottle.response.status = 422
        return SubmitContentError(
            content_id=request.content_id,
            message="submission_type not yet supported",
        )

    return submit_api
