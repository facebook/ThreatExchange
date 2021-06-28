# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import functools
import boto3
import requests
import typing as t
from hmalib.common.message_models import (
    S3ImageSubmission,
    URLImageSubmissionMessage,
)


class ImageSource:
    """
    An interface that is used during hashing to get an image's bytes.
    """

    def get_image_bytes(self, identifier: str) -> bytes:
        """
        Get bytes for the image.
        """
        raise NotImplementedError


@functools.lru_cache(maxsize=None)
def _get_s3_client():
    # memoized so that we don't create a boto3 client unless needed.
    return boto3.client("s3")


class S3BucketImageSource(ImageSource):
    """
    Get images from a single S3 bucket.

    Potential enhancements:
    - Customize retry behavior, with backoff
    - Parameterized credentials rather than relying on boto inference
    """

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket

    def get_image_bytes(self, identifier: str) -> bytes:
        return (
            _get_s3_client()
            .get_object(Bucket=self.bucket, Key=identifier)["Body"]
            .read()
        )


class URLImageSource(ImageSource):
    """
    Simple GET request to get bytes of a URL.

    Potential enhancements:
    - HTTP Retry configuration with backoff
    - HTTP Authorization, Headers
    - Customizable Keep-Alive handling (presently defaults to requests.Session
      defaults)
    """

    def get_image_bytes(self, identifier: str) -> bytes:
        r = requests.get(identifier)
        r.raise_for_status()
        return r.content


def get_image_bytes(
    submission_message: t.Union[URLImageSubmissionMessage, S3ImageSubmission]
):
    """
    Takes a submission_message, identifies how best to get its bytes. Future
    work on re-using sessions for `requests` or any possible optimization must
    go here.
    """
    if isinstance(submission_message, URLImageSubmissionMessage):
        return URLImageSource().get_image_bytes(submission_message.url)
    else:
        return S3BucketImageSource(submission_message.bucket).get_image_bytes(
            submission_message.key
        )
