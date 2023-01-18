# Copyright (c) Meta Platforms, Inc. and affiliates.

import functools
from dataclasses import dataclass
from enum import Enum
import typing as t
import boto3
from datetime import datetime, timedelta

from hmalib.metrics import measure_performance, METRICS_NAMESPACE


@functools.lru_cache(maxsize=None)
def _get_cloudwatch_client():
    return boto3.client("cloudwatch")


def is_publishing_metrics():
    """
    Does this terraform deployment publish metrics to cloudwatch?
    """
    return measure_performance


class MetricTimePeriod(Enum):
    HOURS_24 = "24h"
    HOURS_1 = "1h"
    DAYS_7 = "7d"


def _start_time(period: MetricTimePeriod):
    delta = {
        MetricTimePeriod.HOURS_1: timedelta(hours=1),
        MetricTimePeriod.HOURS_24: timedelta(days=1),
        MetricTimePeriod.DAYS_7: timedelta(days=7),
    }[period] or timedelta(days=1)

    return datetime.now() - delta


def _period(period: MetricTimePeriod):
    """
    Granularity of AWS statistics.
    1 minute for HOURS_1; returns 60 data points
    10 minutes for HOURS_24; returns 144 data points
    1 hour for DAYS_7; return 168 data points
    """
    return {
        MetricTimePeriod.HOURS_1: 60,
        MetricTimePeriod.HOURS_24: 60 * 10,
        MetricTimePeriod.DAYS_7: 60 * 60,
    }[period] or 60 * 10


def _pad_with_None_values(
    graph_data: t.List[t.Tuple[datetime, t.Optional[int]]],
    start_time: datetime,
    end_time: datetime,
) -> t.List[t.Tuple[datetime, t.Optional[int]]]:
    """
    Pad graph data with 0 values if the first or last entries are too far (>60
    seconds) from start or end time respectively.

    Note: Mutates the graph_data parameter, but returns it too.
    """

    if (
        len(graph_data) == 0
        or abs((start_time - graph_data[0][0]).total_seconds()) > 60
    ):
        # If start time and the first graph point have more than a minute, pad
        graph_data.insert(0, (start_time, None))

    if len(graph_data) == 0 or abs((end_time - graph_data[-1][0]).total_seconds()) > 60:
        # If start time and the first graph point have more than a minute, pad
        graph_data.append((end_time, None))

    return graph_data


@dataclass
class CountMetricWithGraph:
    count: int
    graph_data: t.List[t.Tuple[datetime, t.Optional[int]]]


def get_count_with_graph(
    names: t.List[str], time_period: MetricTimePeriod
) -> t.Dict[str, CountMetricWithGraph]:
    """
    Given a time period and a set of metric names, gets the sum of the metric
    over the period and a graphable list of timestamps and values.

    The graph data always contains the start and end time stamps with None values
    to make graphing easier.
    """
    result = {}

    start_time = _start_time(time_period).replace(second=0, microsecond=0, tzinfo=None)
    end_time = datetime.now().replace(second=0, microsecond=0, tzinfo=None)

    for metric_name in names:
        stats = _get_cloudwatch_client().get_metric_statistics(
            Namespace=METRICS_NAMESPACE,
            MetricName=f"{metric_name}-count",
            Statistics=["Sum"],
            StartTime=start_time,
            EndTime=end_time,
            Period=_period(time_period),
        )["Datapoints"]

        total = int(functools.reduce(lambda acc, s: acc + s["Sum"], stats, 0))

        graph_data: t.List[t.Tuple[datetime, t.Optional[int]]] = [
            # Removing tzinfo because you can't work with timezone aware
            # datetime objects and timezone unaware timedelta objects. Either
            # way, eventually, these get decomposed to an epoch value, so this
            # will not hurt.
            # `_pad_with_None_values` expects timezone unaware objects.
            (s["Timestamp"].replace(tzinfo=None), int(s["Sum"]))
            for s in stats
        ]
        graph_data.sort(key=lambda t: t[0])  # Sort by timestamp
        graph_data = _pad_with_None_values(graph_data, start_time, end_time)

        result[metric_name] = CountMetricWithGraph(total, graph_data)

    return result
