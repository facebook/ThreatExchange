# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
S3 Backed Index Management. Offers a menu of indexes.
- S3BackedMD5Index: Exact matches. For MD5.
- S3BackedPDQIndex: For distance matching of fixed width hashes like PDQ. Might
  not be suitable for variable width hashes like TMK. More to come here after I
  understand TMK better. :) -- @schatten
"""

import typing as t
from datetime import datetime
import pickle
import boto3
import functools

from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.signal_type.signal_base import TrivialSignalTypeIndex
from threatexchange.signal_type.pdq.pdq_index import PDQIndex, PDQFlatIndex

from hmalib.common.logging import get_logger
from hmalib import metrics

logger = get_logger(__name__)


@functools.lru_cache(maxsize=None)
def get_s3_client():
    return boto3.client("s3")


class S3PickledIndexStore:
    """
    Store and retrieve indexes as pickled python files on S3.
    """

    INDEXES_PREFIX = "index/"

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name

    def save(self, index):
        with metrics.timer(metrics.names.indexer.upload_index):
            index_file_bytes = pickle.dumps(index)
            get_s3_client().put_object(
                Bucket=self.bucket_name,
                Key=self._get_index_s3_key(index.__class__),
                Body=index_file_bytes,
            )

    def load(self, index_class: t.Type[SignalTypeIndex]):
        with metrics.timer(metrics.names.indexer.download_index):
            index_file_bytes = (
                get_s3_client()
                .get_object(
                    Bucket=self.bucket_name,
                    Key=self._get_index_s3_key(index_class),
                )["Body"]
                .read()
            )
            return pickle.loads(index_file_bytes)

    def get_latest_last_modified(self) -> datetime:
        """
        Get the update time of the newest index.
        """
        objects = get_s3_client().list_objects_v2(
            Bucket=self.bucket_name, Prefix=self.INDEXES_PREFIX
        )
        return max(map(lambda item: item["LastModified"], objects["Contents"]))

    def _get_index_s3_key(self, cls: t.Type[SignalTypeIndex]):
        """
        Uses current class name to get a unique but consistent s3 key for this
        index type.

        The directory structure for the index/ prefix of hashing data bucket is
        governed here. I do not see a reason why anything other than the bucket
        name should be received as an envvar. hmalib, and specifically this
        class should be the only ones reading or writing from that directory.

        Can be convinced otherwise.

        This will result in pretty large names. We are including the module name
        to allow partners to implement and plug in their indexes if they see it
        fit. Eg. Partner specific PDQ index (eg. backed by something other than
        FAISS) can co-exist with our own.

        ours:  index/threatexchange.signal_type.pdq.index.FlatPDQIndex.index
        their: index/partnername.integrity.indexers.CustomPDQIndex.index
        """
        return f"{self.INDEXES_PREFIX}{cls.__module__}.{cls.__name__}.index"
