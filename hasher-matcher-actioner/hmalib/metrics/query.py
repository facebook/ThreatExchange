# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import functools
from dataclasses import dataclass
from enum import Enum
import typing as t
import boto3
from datetime import datetime, timedelta

from . import measure_performance, METRICS_NAMESPACE


@functools.lru_cache(maxsize=None)
def _get_cloudwatch_client():
    return boto3.client("cloudwatch")


def is_publishing_metrics():
    """
    Does this terraform deployment publish metrics to cloudwatch?
    """
    return measure_performance


class MetricTimePeriod:
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


@dataclass
class CountMetricWithGraph:
    count: int
    graph_data: t.List[t.Tuple[datetime, int]]


def get_count_with_graph(
    names: t.List[str], time_period: MetricTimePeriod
) -> t.Dict[str, CountMetricWithGraph]:
    """
    Given a time period and a set of metric names, gets the sum of the metric
    over the period and a graphable list of timestamps and values.
    """
    result = {}

    for metric_name in names:
        stats = _get_cloudwatch_client().get_metric_statistics(
            Namespace=METRICS_NAMESPACE,
            MetricName=f"{metric_name}-count",
            Statistics=["Sum"],
            StartTime=_start_time(time_period),
            EndTime=datetime.now(),
            Period=_period(time_period),
        )["Datapoints"]

        total = int(functools.reduce(lambda acc, s: acc + s["Sum"], stats, 0))

        graph_data = [(s["Timestamp"], int(s["Sum"])) for s in stats]
        graph_data.sort(key=lambda t: t[0])  # Sort by timestamp

        result[metric_name] = CountMetricWithGraph(total, graph_data)

    return result
