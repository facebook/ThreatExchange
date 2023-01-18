# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
from collections import defaultdict
import os
from functools import lru_cache
from mypy_boto3_dynamodbstreams.type_defs import GetRecordsOutputTypeDef, RecordTypeDef
import boto3

from hmalib.common.models.content import ContentObject
from hmalib.common.models.count import AggregateCount, CountBuffer
from hmalib.common.logging import get_logger
from hmalib.common.models.models_base import DynamoDBItem

logger = get_logger(__name__)

# Which table is this stream processor tailing?
SOURCE_TABLE_TYPE = os.environ["SOURCE_TABLE_TYPE"]

# Which table do we write counts to.
COUNTS_TABLE_NAME = os.environ["COUNTS_TABLE_NAME"]


@lru_cache(maxsize=None)
def get_counts_table():
    return boto3.resource("dynamodb").Table(COUNTS_TABLE_NAME)


class BaseTableStreamCounter:
    @classmethod
    def table_type(cls) -> str:
        """
        DDB Streams do not necessarily pass the name of the table from which the
        event is sourced. This means we have to use some tricks.

        We create separate lambda functions in AWS for each table that needs a
        stream. Both the lambda functions use the same code, but an environment
        variable (SOURCE_TABLE_TYPE) is used to notify the lambda code which
        table generated the event.

        This is an enum. The values of this can be found in terraform/main.tf
        module "counters", attribute for_each.

        A subclass impl of this method should return one of those enum values.
        If you are adding a new table, you'll need to:
        a) add it to terraform/main.tf:module "counters":attribute for_each
        b) add a subclass of this class "BaseTableStreamCounter"
        c) add it to ENABLED_STREAM_COUNTERS in this module
           (hmalib.lambdas.ddb_stream_counter)
        """
        raise NotImplementedError

    @classmethod
    def update_increments_for_records(
        cls, records: t.List[RecordTypeDef], count_buffer: CountBuffer
    ):
        """
        Given a list of streamed ddb records, and a buffer, processes the
        records and calls count_buffer.inc_*/dec_* methods as appropriate.

        At the end, will flush the buffer too.
        """
        raise NotImplementedError


class PipelineTableStreamCounter(BaseTableStreamCounter):
    @classmethod
    def table_type(cls):
        return "HMADataStore"

    @classmethod
    def update_increments_for_records(
        cls, records: t.List[RecordTypeDef], count_buffer: CountBuffer
    ):
        """
        Given a list of streamed ddb records, and a buffer, processes the
        records and calls count_buffer.inc_*/dec_* methods as appropriate.

        At the end, will flush the buffer too.
        """
        for record in records:
            if record["eventName"] != "INSERT":
                # We only want to track create events.
                continue

            pk: str = record["dynamodb"]["Keys"]["PK"]["S"]
            sk: str = record["dynamodb"]["Keys"]["SK"]["S"]
            # The raw stream values have a different schema than what is returned by boto3 meaning
            # they can't be deserialized into one of the HMA datamodels using existing functionality.
            inserted_record = record["dynamodb"]["NewImage"]

            # TODO These should maybe have a strong connection to the objects instead of class constants
            # otherwise changes to the object might not correctly update these count checks
            if sk == ContentObject.CONTENT_STATIC_SK:
                count_buffer.inc_aggregate(AggregateCount.PipelineNames.submits)
                if (
                    content_type := inserted_record.get("ContentType", {}).get("S")
                ) is not None:
                    count_buffer.inc_parameterized(
                        AggregateCount.PipelineNames.submits,
                        "content_type",
                        content_type,
                    )
            elif sk.startswith(DynamoDBItem.TYPE_PREFIX):
                # note hashes should always match submits (submits == hashes)
                count_buffer.inc_aggregate(AggregateCount.PipelineNames.hashes)
                if (
                    signal_type := inserted_record.get("SignalType", {}).get("S")
                ) is not None:
                    count_buffer.inc_parameterized(
                        AggregateCount.PipelineNames.hashes, "signal_type", signal_type
                    )
            elif sk.startswith(DynamoDBItem.SIGNAL_KEY_PREFIX):
                count_buffer.inc_aggregate(AggregateCount.PipelineNames.matches)
                if (
                    signal_source := inserted_record.get("SignalSource", {}).get("S")
                ) is not None:
                    signal_id = sk.split("#")[-1]
                    count_buffer.inc_parameterized(
                        AggregateCount.PipelineNames.matches, signal_source, signal_id
                    )

        count_buffer.flush()


class BanksTableStreamCounter(BaseTableStreamCounter):
    @classmethod
    def table_type(cls) -> str:
        return "HMABanks"


ENABLED_STREAM_COUNTERS = {
    cls.table_type(): cls
    for cls in [PipelineTableStreamCounter, BanksTableStreamCounter]
}

current_stream_counter = ENABLED_STREAM_COUNTERS[SOURCE_TABLE_TYPE]


def lambda_handler(event: GetRecordsOutputTypeDef, _context):
    """
    # How do entity counts work in HMA?

    Without blocking ddb edits. So we do it as a stream processor. Lambda
    ddb_stream_counter will do the following:
    a) listen to stream updates to all configured datastores
    b) determine if the update matches increment or decrement condition for any
    tracked counts.
    c) Update those counts.

    Counts are stored in a separate dynamodb table. This is done so that we
    don't accidentally end up in an infinite loop of updates and lambda
    invocations. To make matters iron-clad, the stream counter lambda does not
    have write permission on any of the source tables.
    """
    counts_table = get_counts_table()
    count_buffer = CountBuffer(counts_table)
    current_stream_counter.update_increments_for_records(event["Records"], count_buffer)
