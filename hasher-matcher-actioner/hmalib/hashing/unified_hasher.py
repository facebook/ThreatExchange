# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import json
from dataclasses import dataclass
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_sqs.client import SQSClient

from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import SignalType, BytesHasher

from hmalib.common.logging import get_logger
from hmalib.common.mappings import HMASignalTypeMapping
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
        signal_type_mapping: HMASignalTypeMapping,
        output_queue_url: str,
    ):
        self.signal_type_mapping = signal_type_mapping
        self.output_queue_url = output_queue_url

    def supports(self, content_type: t.Type[ContentType]) -> bool:
        """
        Can this hasher produce signals for content of `content_type`?

        Right now, just verifies whether signal_type_mapping brings in this
        type. In the future should say 'no' for unhashable content like PDFs or
        raw-text.
        """
        return bool(
            self.signal_type_mapping.get_content_type_enforce(content_type.get_name())
        )

    def get_hashes(
        self, content_type: t.Type[ContentType], bytes_: bytes
    ) -> t.Generator[ContentSignal, None, None]:
        """
        Yields signals for content_type.
        """
        for (
            signal_type
        ) in self.signal_type_mapping.get_supported_signal_types_for_content(
            content_type
        ):
            if issubclass(signal_type, BytesHasher):
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
