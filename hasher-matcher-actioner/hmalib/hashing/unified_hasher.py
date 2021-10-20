# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
import json
from dataclasses import dataclass
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_sqs.client import SQSClient

from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import SignalType, BytesHasher

from hmalib.common.logging import get_logger
from hmalib.common.models.pipeline import PipelineHashRecord
from hmalib import metrics

logger = get_logger(__name__)


@dataclass
class ContentSignal:
    """
    Envelope for a signal type and signal's value. Has been extracted from a
    piece of content.

    TODO: assumption that a signal value can only be string is inaccurate. Even
    simple algorithms like PDQ emit a tuple. Quality and Hash value.

    Need to figure out a way for this to be extensible or flexible for all kinds
    of hashes.
    """

    content_type: t.Type[ContentType]
    signal_type: t.Type[SignalType]
    signal_value: str


class UnifiedHasher:
    """
    A hasher that can generate signal_type from content_type as long as they are
    in its 'supported_signal_types' and 'supported_content_types' lists
    respectively.

    The workhorse is get_hashes() which is a generator for SignalValues.

    Why this class, why not do everything in the hasher lambda itself?
    a) the lambda is aws specific, want to keep business logic out of it
    b) to allow different configurations of the generic hasher to exist without
       rewriting lambdas. Imagine the same lambda python function has two AWS
       lambda instances. The only difference is an environment variable which
       allows different signal or content types to be processable. For the video
       processor, we allocate more memory and compute etc.
    """

    def __init__(
        self,
        supported_content_types: t.List[t.Type[ContentType]],
        supported_signal_types: t.List[t.Type[SignalType]],
        output_queue_url: str,
    ):
        self.supported_content_types = supported_content_types

        # Not enforced in typing because python does not yet have t.Intersect,
        # but all supported_signal_types must also implement BytesHasher
        assert all([issubclass(t, BytesHasher) for t in supported_signal_types])

        self.supported_signal_types = supported_signal_types

        self.output_queue_url = output_queue_url

    def supports(self, content_type: t.Type[ContentType]) -> bool:
        """
        Can this hasher produce signals for content of `content_type`?
        """
        return content_type in self.supported_content_types

    def get_hashes(
        self, content_type: t.Type[ContentType], bytes_: bytes
    ) -> t.Generator[ContentSignal, None, None]:
        """
        Yields signals for content_type.
        """
        for signal_type in content_type.get_signal_types():
            if signal_type in self.supported_signal_types and issubclass(
                signal_type, BytesHasher
            ):
                with metrics.timer(metrics.names.hasher.hash(signal_type.get_name())):
                    try:
                        hash_value = signal_type.hash_from_bytes(bytes_)
                    except Exception:
                        logger.exception(
                            "Encountered exception while trying to hash_from_bytes. Unable to hash content."
                        )
                        continue

                yield ContentSignal(content_type, signal_type, hash_value)

    def write_hash_record(self, table: Table, hash_record: PipelineHashRecord):
        """
        Once a content signal has been created, write its corresponding hash
        record. These records can be used to do retroaction in case a new signal
        is obtained from sources.
        """
        with metrics.timer(metrics.names.hasher.write_record):
            hash_record.write_to_table(table)

    def publish_hash_message(
        self, sqs_client: SQSClient, hash_record: PipelineHashRecord
    ):
        """
        Once you've written the hash record, publish a message to the matcher's
        input queue.
        """
        with metrics.timer(metrics.names.hasher.publish_message):
            sqs_client.send_message(
                QueueUrl=self.output_queue_url,
                MessageBody=json.dumps(hash_record.to_sqs_message()),
            )
