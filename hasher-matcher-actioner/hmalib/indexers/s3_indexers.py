# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
S3 Backed Index Management. Offers a menu of indexes.
- S3BackedMD5Index: Exact matches. For MD5.
- S3BackedPDQIndex: For distance matching of fixed width hashes like PDQ. Might
  not be suitable for variable width hashes like TMK. More to come here after I
  understand TMK better. :) -- @schatten
"""

from datetime import datetime
import pickle
import boto3
import functools
from mypy_boto3_s3.service_resource import Bucket
from mypy_boto3_s3.type_defs import MetricsAndOperatorTypeDef
from threatexchange.signal_type.signal_base import TrivialSignalTypeIndex
from threatexchange.signal_type.pdq.pdq_index import PDQIndex, PDQFlatIndex

from hmalib.common.logging import get_logger
from hmalib import metrics

logger = get_logger(__name__)


@functools.lru_cache(maxsize=None)
def get_s3_client():
    return boto3.client("s3")


class S3BackedInstrumentedIndexMixin:
    """
    Contains behavior common to all indexes that store their data on S3. Do not
    override init. That must be delegated to a SignalTypeIndex implementation.

    Also overrides methods to wrap instrumentation with hmalib.metrics library.
    """

    INDEXES_PREFIX = "index/"

    def save(self, bucket_name: str):
        with metrics.timer(metrics.names.indexer.upload_index):
            index_file_bytes = pickle.dumps(self)
            get_s3_client().put_object(
                Bucket=bucket_name,
                Key=self.__class__._get_index_s3_key(),
                Body=index_file_bytes,
            )

    @classmethod
    def load(cls, bucket_name: str):
        with metrics.timer(metrics.names.indexer.download_index):
            index_file_bytes = (
                get_s3_client()
                .get_object(Bucket=bucket_name, Key=cls._get_index_s3_key())["Body"]
                .read()
            )
            return pickle.loads(index_file_bytes)

    def get_index_class_name(self) -> str:
        """
        Name to help identify the index being used in HMA logs.
        """
        return self.__class__.__name__

    @classmethod
    def get_index_max_distance(cls) -> int:
        """
        Helper to distinguish if the next should be used based on configured thersholds.
        Defaults to zero (i.e. only exact matches supported)
        """
        return 0

    @classmethod
    def get_latest_last_modified(cls, bucket_name: str) -> datetime:
        """
        Get the update time of the newest index.
        """
        objects = get_s3_client().list_objects_v2(
            Bucket=bucket_name, Prefix=cls.INDEXES_PREFIX
        )
        return max(map(lambda item: item["LastModified"], objects["Contents"]))

    @classmethod
    def _get_index_s3_key(cls):
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

        ours:  index/hmalib.indexers.s3_indexers.S3BackedPDQIndex.index
        their: index/partnername.integrity.indexers.CustomPDQIndex.index
        """
        return f"{cls.INDEXES_PREFIX}{cls.__module__}.{cls.__name__}.index"


class S3BackedMD5Index(TrivialSignalTypeIndex, S3BackedInstrumentedIndexMixin):
    """
    DO NOT OVERRIDE __init__(). Let TrivialSignalTypeIndex provide that.
    """

    pass


class S3BackedPDQIndex(PDQIndex, S3BackedInstrumentedIndexMixin):
    """
    DO NOT OVERRIDE __init__(). Let PDQIndex provide that.
    """

    pass

    @classmethod
    def get_index_max_distance(cls) -> int:
        return cls.get_match_threshold()


class S3BackedPDQFlatIndex(PDQFlatIndex, S3BackedInstrumentedIndexMixin):
    """
    DO NOT OVERRIDE __init__(). Let PDQFlatIndex provide that.
    """

    @classmethod
    def get_index_max_distance(cls) -> int:
        return cls.get_match_threshold()
