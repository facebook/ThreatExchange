# Copyright (c) Meta Platforms, Inc. and affiliates.

""" Refer to hmalib.lambdas.ddb_stream_counter.lambda_handler's doc string to
understand how these models are used. """
import typing as t
from collections import defaultdict

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import Table


class BaseCount:
    """
    Defines a single count value.
    """

    def get_pkey(self) -> str:
        """
        Get partition key for this count.
        """
        raise NotImplementedError

    def get_skey(self) -> str:
        """
        Get sort key for this count.
        """
        raise NotImplementedError

    def get_value(self, table: Table) -> int:
        """
        Get current value for the counter.
        """
        return t.cast(
            int,
            table.get_item(Key={"PK": self.get_pkey(), "SK": self.get_skey()})
            .get("Item", {})
            .get("CurrentCount", 0),
        )

    def inc(self, table: Table, by=1):
        """
        Increment count. Default by 1, unless specified.
        """
        table.update_item(
            Key={"PK": self.get_pkey(), "SK": self.get_skey()},
            UpdateExpression="SET CurrentCount = if_not_exists(CurrentCount, :zero) + :by",
            ExpressionAttributeValues={":by": by, ":zero": 0},
        )

    def dec(self, table: Table, by=1):
        """
        Increment count. Default by 1, unless specified.
        """
        table.update_item(
            Key={"PK": self.get_pkey(), "SK": self.get_skey()},
            UpdateExpression="SET CurrentCount = if_not_exists(CurrentCount, :zero) - :by",
            ExpressionAttributeValues={":by": by, ":zero": 0},
        )


class AggregateCount(BaseCount):
    """
    A "total" count. It is possible for some entities to have TBD hourly as well as
    aggregate counts. eg. Give me all matches today, but also keep track of the
    total number of matches we have ever done.
    """

    class PipelineNames:

        # How many pieces of content were submitted?
        submits = "hma.pipeline.submits"

        # How many pieces of content created a hash record?
        hashes = "hma.pipeline.hashes"

        # How many match object recorded?
        matches = "hma.pipeline.matches"

    def __init__(self, of: str):
        self.of = of

    @staticmethod
    def _get_pkey_for_aggregate(of: str) -> str:
        return f"aggregate#{of}"

    @staticmethod
    def _get_skey_for_aggregate() -> str:
        return "aggregate_count"

    def get_pkey(self) -> str:
        return self._get_pkey_for_aggregate(self.of)

    def get_skey(self) -> str:
        return self._get_skey_for_aggregate()


class ParameterizedCount(BaseCount):
    """
    Allows you to do aggregate counts, with a parameter. An example would be
    matches per privacy group.

    At this point, only supports a single parameter value.

    Think about it as
        ParameterizedCount(of="hma.pipeline.matches", by="privacy_group"), value="4567896456789000976"))
    or  ParameterizedCount(of="hma.pipeline.hashes", by="content_type", value="photo")
    or  ParameterizedCount(of="hma.pipeline.hashes", by="signal_type", value="pdq")
    """

    SKEY_PREFIX = "val#"
    SKEY_PREFIX_LENGTH = len(SKEY_PREFIX)

    def __init__(self, of: str, by: str, value: str, cached_value: int = None):
        """
        You may provide a cached value if this object is getting retrieved from
        the database. Note, this does not in any way change the actual value in
        the database. It only saves a database call if you are using get_value()
        immediately after.
        """

        self.of = of
        self.by = by
        self.value = value
        self._cached_value = cached_value

    def get_value(self, table: Table) -> int:
        """
        If cached_value is set to a non-None value, return it, else make a
        database call to get the answer. This is useful when you are getting a
        list of parameterized counts using `ParameterizedCount.get_all()`
        """
        if self._cached_value:
            return self._cached_value

        return super().get_value(table)

    @classmethod
    def get_all(cls, of: str, by: str, table: Table) -> t.List["ParameterizedCount"]:
        return [
            cls(
                of,
                by,
                value=t.cast(str, item.get("SK"))[
                    cls.SKEY_PREFIX_LENGTH :
                ],  # strip the "val#" portion
                cached_value=t.cast(int, item.get("CurrentCount", 0)),
            )
            for item in table.query(
                ScanIndexForward=True,
                KeyConditionExpression=Key("PK").eq(
                    cls._get_pkey_for_parameterized(of, by)
                ),
            )["Items"]
        ]

    @staticmethod
    def _get_pkey_for_parameterized(of: str, by: str) -> str:
        return f"parameterized#{of}#by#{by}"

    @classmethod
    def _get_skey_for_parameterized(cls, by: str, value: str) -> str:
        return f"{cls.SKEY_PREFIX}{value}"

    def get_pkey(self) -> str:
        return self._get_pkey_for_parameterized(self.of, self.by)

    def get_skey(self) -> str:
        return self._get_skey_for_parameterized(self.by, self.value)


class CountBuffer:
    """
    A buffer that for increments to the variety of count types. Must call
    buffer.flush() at the end to flush everything to ddb.

    buffer = CountBuffer(ddb_table)

    buffer.inc_aggregate("hma.pipeline.matches")
    buffer.inc_parameterized("hma.pipeline.submit", by="content_type",
    value="photo")
    """

    def __init__(self, table: Table):
        self.table = table
        self.aggregate_deltas: t.DefaultDict = defaultdict(lambda: 0)
        self.parameterized_deltas: t.DefaultDict = defaultdict(lambda: 0)

    def inc_aggregate(self, of: str):
        """
        Increment an aggregate counter.
        """
        self.aggregate_deltas[of] += 1

    def dec_aggregate(self, of: str):
        """
        Decrement an aggregate counter.
        """
        self.aggregate_deltas[of] -= 1

    def inc_parameterized(self, of: str, by: str, value: str):
        """
        Increment a parameterized counter.

        eg. buffer.inc_parameterized("hma.pipeline.submit", by="content_type", value="photo")
        """
        self.parameterized_deltas[(of, by, value)] += 1

    def dec_parameterized(self, of: str, by: str, value: str):
        """
        Decrement a parameterized counter.

        eg. buffer.dec_parameterized("hma.pipeline.submit", by="content_type", value="photo")
        """
        self.parameterized_deltas[(of, by, value)] -= 1

    def flush(self):
        """
        Write all counters remaining in the buffer. Since we do not autoflush
        yet, this may take some time.

        TODO: Make this into batch calls to dynamodb so it is performant. Right
        now, we iterate through all increments and make individual calls to
        dynamodb. This is partially because BaseCount defines inc() method. Can
        this be extracted out such that instead of doing one ddb write per
        BaseCount, we can batch the DDB writes and do a single BatchWriteItem call?
        https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BatchWriteItem.html
        """
        for name, increment_by in self.aggregate_deltas.items():
            if increment_by > 0:
                AggregateCount(str(name)).inc(self.table, increment_by)
            elif increment_by < 0:
                AggregateCount(str(name)).dec(self.table, abs(increment_by))
        # reset flushed buffer
        self.aggregate_deltas = defaultdict(lambda: 0)

        for delta_tuple, increment_by in self.parameterized_deltas.items():
            of, by, value = delta_tuple

            if increment_by > 0:
                ParameterizedCount(of, by, value).inc(self.table, increment_by)
            elif increment_by < 0:
                ParameterizedCount(of, by, value).dec(self.table, increment_by)
        # reset flushed buffer
        self.parameterized_deltas = defaultdict(lambda: 0)
