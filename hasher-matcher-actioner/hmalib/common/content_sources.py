# Copyright (c) Meta Platforms, Inc. and affiliates.

import functools
import boto3
import requests
import typing as t


class ContentSource:
    """
    An interface that is used during hashing to get bytes from a URL. Subclasses
    may be potentially used to *store* the bytes at submission.
    """

    def get_bytes(self, identifier: str) -> bytes:
        """
        Get bytes for an image/video/etc.
        """
        raise NotImplementedError


@functools.lru_cache(maxsize=None)
def _get_s3_client():
    # memoized so that we don't create a boto3 client unless needed.
    return boto3.client("s3")


class S3BucketContentSource(ContentSource):
    """
    Get images or videos from a single S3 bucket. Formalizes the convention of
    including the content_id in the S3 key. If you find yourself relying on the
    structure of the s3 key to do any inference, consider moving that piece of
    code here.

    Potential enhancements:
    - Customize retry behavior, with backoff
    - Parameterized credentials rather than relying on boto inference
    """

    def __init__(self, bucket: str, image_prefix: str) -> None:
        self.bucket = bucket
        self.image_prefix = image_prefix

    def get_bytes(self, content_id: str) -> bytes:
        return (
            _get_s3_client()
            .get_object(Bucket=self.bucket, Key=self.get_s3_key(content_id))["Body"]
            .read()
        )

    @staticmethod
    def get_content_id_from_s3_key(s3_key: str, image_prefix: str) -> str:
        """
        Useful when you have received an s3 event, so you don't have content_id,
        but need to infer it.
        """
        return s3_key[len(image_prefix) :]

    def get_s3_key(self, content_id) -> str:
        return f"{self.image_prefix}{content_id}"

    def put_image_bytes(self, content_id: str, contents: bytes):
        """
        This is not part of the ImageSource interface. But S3 keys have some
        built in structure that must be formalized. See class docstring for
        more.
        """
        _get_s3_client().put_object(
            Body=contents, Bucket=self.bucket, Key=self.get_s3_key(content_id)
        )


class URLContentSource(ContentSource):
    """
    Simple GET request to get bytes of a URL.

    Potential enhancements:
    - HTTP Retry configuration with backoff
    - HTTP Authorization, Headers
    - Customizable Keep-Alive handling (presently defaults to requests.Session
      defaults)
    """

    def get_bytes(self, identifier: str) -> bytes:
        r = requests.get(identifier)
        r.raise_for_status()
        return r.content
