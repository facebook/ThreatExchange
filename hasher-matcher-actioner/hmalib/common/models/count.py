# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

""" Refer to hmalib.lambdas.ddb_stream_counter.lambda_handler's doc string to
understand how these models are used. """
import typing as t
from mypy_boto3_dynamodb.service_resource import Table


class BaseCount:
    """
    Defines a single count value.
    """

    def get_pkey(self) -> str:
        """Get partition key for this count."""
        raise NotImplementedError

    def get_skey(self) -> str:
        """Get sort key for this count."""
        raise NotImplementedError

    def get_value(self, table: Table) -> int:
        """Get current value for the counter."""
        return t.cast(
            int,
            table.get_item(Key={"PK": self.get_pkey(), "SK": self.get_skey()})
            .get("Item", {})
            .get("CurrentCount", 0),
        )

    def inc(self, table: Table, by=1):
        """Increment count. Default by 1, unless specified."""
        table.update_item(
            Key={"PK": self.get_pkey(), "SK": self.get_skey()},
            UpdateExpression="SET CurrentCount = if_not_exists(CurrentCount, :zero) + :by",
            ExpressionAttributeValues={":by": by, ":zero": 0},
        )

    def dec(self, table: Table, by=1):
        """Increment count. Default by 1, unless specified."""
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
