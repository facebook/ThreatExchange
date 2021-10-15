# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
from collections import defaultdict
import os
from functools import lru_cache
from mypy_boto3_dynamodbstreams.type_defs import GetRecordsOutputTypeDef, RecordTypeDef
import boto3

from hmalib.common.models.content import ContentObject
from hmalib.common.models.count import AggregateCount
from hmalib.common.logging import get_logger
from hmalib.common.models.models_base import DynamoDBItem

logger = get_logger(__name__)

# Which table is this stream processor tailing?
SOURCE_TABLE_NAME = os.environ["SOURCE_TABLE_NAME"]

# Which table do we write counts to.
COUNTS_TABLE_NAME = os.environ["COUNTS_TABLE_NAME"]


@lru_cache(maxsize=None)
def get_counts_table():
    return boto3.resource("dynamodb").Table(COUNTS_TABLE_NAME)


class BaseTableStreamCounter:
    @classmethod
    def table_name(cls) -> str:
        raise NotImplementedError

    @staticmethod
    def get_increments_for_records(
        records: t.List[RecordTypeDef],
    ) -> t.Dict[AggregateCount, int]:
        """
        Given a list of streamed ddb records, returns a map of BaseCounts -> the
        value by which they should be incremented. Negative increment implies
        decrement.
        """
        raise NotImplementedError


class PipelineTableStreamCounter(BaseTableStreamCounter):
    @classmethod
    def table_name(cls):
        return "HMADataStore"

    @classmethod
    def get_increments_for_records(
        cls,
        records: t.List[RecordTypeDef],
    ) -> t.Dict[AggregateCount, int]:
        """
        Given a list of streamed ddb records, returns a map of BaseCounts -> the
        value by which they should be incremented. Negative increment implies
        decrement.
        """
        result: defaultdict = defaultdict(lambda: 0)
        for record in records:
            if record["eventName"] != "INSERT":
                # We only want to track create events.
                continue

            pk: str = record["dynamodb"]["Keys"]["PK"]["S"]
            sk: str = record["dynamodb"]["Keys"]["SK"]["S"]

            # TODO These should maybe have a strong connection to the objects instead of class constants
            # otherwise changes to the object might not correctly update these count checks
            if sk == ContentObject.CONTENT_STATIC_SK:
                result[AggregateCount.PipelineNames.submits] += 1
            elif sk.startswith(DynamoDBItem.TYPE_PREFIX):
                # note hashes should always match submits (submits == hashes)
                result[AggregateCount.PipelineNames.hashes] += 1
            elif sk.startswith(DynamoDBItem.SIGNAL_KEY_PREFIX):
                result[AggregateCount.PipelineNames.matches] += 1

        return dict(result)


class BanksTableStreamCounter(BaseTableStreamCounter):
    @classmethod
    def table_name(cls) -> str:
        return "HMABanks"


ENABLED_STREAM_COUNTERS = {
    cls.table_name(): cls
    for cls in [PipelineTableStreamCounter, BanksTableStreamCounter]
}

current_stream_counter = ENABLED_STREAM_COUNTERS[SOURCE_TABLE_NAME]


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
    counts: t.Dict[
        AggregateCount, int
    ] = current_stream_counter.get_increments_for_records(event["Records"])

    counts_table = get_counts_table()

    for count in counts:
        # TODO convert this to a batch write.
        increment_by = counts[count]
        if increment_by > 0:
            AggregateCount(str(count)).inc(counts_table, increment_by)
        elif increment_by < 0:
            AggregateCount(str(count)).dec(counts_table, abs(increment_by))
