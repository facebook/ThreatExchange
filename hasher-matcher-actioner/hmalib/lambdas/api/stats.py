# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle
import datetime

from dataclasses import dataclass, asdict, field
from enum import Enum
import typing as t
from mypy_boto3_dynamodb.service_resource import Table

from hmalib.common.logging import get_logger
from hmalib import metrics
from hmalib.metrics import query as metrics_query
from hmalib.metrics.query import is_publishing_metrics

from .middleware import jsoninator, JSONifiable

logger = get_logger(__name__)


class StatNameChoices(Enum):
    HASHES = "hashes"
    MATCHES = "matches"
    ACTIONS_TAKEN = "actions"


@dataclass
class StatsCard(JSONifiable):
    stat_name: StatNameChoices
    number: int
    time_span: metrics_query.MetricTimePeriod
    graph_data: t.List[t.Tuple[datetime.datetime, int]]
    last_updated: str = field(default_factory=datetime.datetime.now)

    def to_json(self) -> t.Dict:
        result = asdict(self)
        result.update(
            last_updated=int(self.last_updated.timestamp()),
            stat_name=self.stat_name.value,
            time_span=self.time_span.value,
            graph_data=[
                [int(datum[0].timestamp()), datum[1]] for datum in self.graph_data
            ],
        )
        return result


@dataclass
class DefaultStatsResponse(JSONifiable):
    """
    The first stats page. Contains most stats you need to understand how things
    are at a high level.
    """

    stats: t.List[StatsCard] = field(default_factory=list)

    def to_json(self) -> t.Dict:
        return {"cards": [s.to_json() for s in self.stats]}


def get_stats_api(dynamodb_table: Table) -> bottle.Bottle:
    """
    Closure for all dependencies for the stats APIs.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/stats/'
    stats_api = bottle.Bottle()

    @stats_api.get("/", apply=[jsoninator])
    def default_stats() -> DefaultStatsResponse:
        """
        If measure performance tfvar/os.env is true, it returns stats, else,
        returns 404. A 404 should be surfaced by clients with instructions on
        how to enable metrics tracking.

        The graph_data always contains the start_time and end_time timestamps
        with 0 values to make graphing easier.
        """
        if not is_publishing_metrics():
            return bottle.abort(404, "This HMA instance is not publishing metrics.")

        time_span_arg = bottle.request.query.time_span
        metric_time_period = {
            "24h": metrics_query.MetricTimePeriod.HOURS_24,
            "1h": metrics_query.MetricTimePeriod.HOURS_1,
            "7d": metrics_query.MetricTimePeriod.DAYS_7,
        }.get(time_span_arg, metrics_query.MetricTimePeriod.HOURS_24)

        count_with_graphs = metrics_query.get_count_with_graph(
            [
                metrics.names.pdq_hasher_lambda.hash,
                metrics.names.pdq_matcher_lambda.search_index,
                # metrics.names.actionining stuff.
            ],
            metric_time_period,
        )

        return DefaultStatsResponse(
            [
                StatsCard(
                    StatNameChoices.HASHES,
                    count_with_graphs[metrics.names.pdq_hasher_lambda.hash].count,
                    metric_time_period,
                    count_with_graphs[metrics.names.pdq_hasher_lambda.hash].graph_data,
                ),
                StatsCard(
                    StatNameChoices.MATCHES,
                    count_with_graphs[
                        metrics.names.pdq_matcher_lambda.search_index
                    ].count,
                    metric_time_period,
                    count_with_graphs[
                        metrics.names.pdq_matcher_lambda.search_index
                    ].graph_data,
                ),
            ]
        )

    return stats_api
