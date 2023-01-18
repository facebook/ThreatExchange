# Copyright (c) Meta Platforms, Inc. and affiliates.

import bottle
import datetime

from dataclasses import dataclass, asdict, field
import typing as t
from mypy_boto3_dynamodb.service_resource import Table

from hmalib.common.logging import get_logger
from hmalib import metrics
from hmalib.metrics import query as metrics_query
from hmalib.metrics.query import is_publishing_metrics
from hmalib.common.models.count import AggregateCount

from hmalib.lambdas.api.middleware import (
    jsoninator,
    JSONifiable,
    SubApp,
)

logger = get_logger(__name__)


@dataclass
class StatsCard(JSONifiable):
    time_span_count: int
    time_span: metrics_query.MetricTimePeriod
    graph_data: t.List[t.Tuple[datetime.datetime, t.Optional[int]]]
    last_updated: datetime.datetime = field(default_factory=datetime.datetime.now)

    def to_json(self) -> t.Dict:
        result = asdict(self)
        result.update(
            last_updated=int(self.last_updated.timestamp()),
            time_span=self.time_span.value,
            graph_data=[
                [int(datum[0].timestamp()), datum[1]] for datum in self.graph_data
            ],
        )
        return result


@dataclass
class StatResponse(JSONifiable):
    """
    Represents a single stat.
    """

    stat: StatsCard

    def to_json(self) -> t.Dict:
        return {"card": self.stat.to_json()}


@dataclass
class AggregateCountResponse(JSONifiable):
    """
    Represents a simple set of Aggregate counts
    """

    counts: t.Dict[str, int]

    def to_json(self) -> t.Dict:
        return asdict(self)


def get_stats_api(counts_table: Table) -> bottle.Bottle:
    """
    Closure for all dependencies for the stats APIs.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/stats/'
    stats_api = SubApp()

    stat_name_to_metric = {
        "hashes": metrics.names.pdq_hasher_lambda.hash,
        "matches": metrics.names.pdq_matcher_lambda.write_match_record,
    }

    @stats_api.get("/", apply=[jsoninator])
    def default_stats() -> StatResponse:
        """
        If measure performance tfvar/os.env is true, it returns stats, else,
        returns 404. A 404 should be surfaced by clients with instructions on
        how to enable metrics tracking.

        The graph_data always contains the start_time and end_time timestamps
        with 0 values to make graphing easier.
        """
        if not is_publishing_metrics():
            return bottle.abort(404, "This HMA instance is not publishing metrics.")

        if (
            not bottle.request.query.stat_name
            or bottle.request.query.stat_name not in stat_name_to_metric
        ):
            return bottle.abort(
                400,
                f"Must specifiy stat_name in query parameters. Must be one of {stat_name_to_metric.keys()}",
            )

        metric = stat_name_to_metric[bottle.request.query.stat_name]

        time_span_arg = bottle.request.query.time_span
        metric_time_period = {
            "24h": metrics_query.MetricTimePeriod.HOURS_24,
            "1h": metrics_query.MetricTimePeriod.HOURS_1,
            "7d": metrics_query.MetricTimePeriod.DAYS_7,
        }.get(time_span_arg, metrics_query.MetricTimePeriod.HOURS_24)

        count_with_graphs = metrics_query.get_count_with_graph(
            [metric],
            metric_time_period,
        )

        return StatResponse(
            StatsCard(
                count_with_graphs[metric].count,
                metric_time_period,
                count_with_graphs[metric].graph_data,
            )
        )

    @stats_api.get("/counts/", apply=[jsoninator])
    def aggregate_counts() -> AggregateCountResponse:
        """
        return the set of aggregate_counts
        """
        if not is_publishing_metrics():
            return bottle.abort(404, "This HMA instance is not publishing metrics.")

        PIPELINE_COUNTS_TO_SURFACE = [
            AggregateCount.PipelineNames.submits,
            AggregateCount.PipelineNames.hashes,
            AggregateCount.PipelineNames.matches,
        ]

        return AggregateCountResponse(
            {
                count_name: int(AggregateCount(count_name).get_value(counts_table))
                for count_name in PIPELINE_COUNTS_TO_SURFACE
            }
        )

    return stats_api
