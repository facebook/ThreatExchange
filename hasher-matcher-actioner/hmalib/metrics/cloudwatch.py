# Copyright (c) Meta Platforms, Inc. and affiliates.

import boto3
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import typing as t
import logging

from hmalib import metrics

logger = logging.getLogger(__name__)


class AWSCloudWatchUnit(Enum):
    Seconds = "Seconds"
    Microseconds = "Microseconds"
    Milliseconds = "Milliseconds"
    Bytes = "Bytes"
    Kilobytes = "Kilobytes"
    Megabytes = "Megabytes"
    Gigabytes = "Gigabytes"
    Terabytes = "Terabytes"
    Bits = "Bits"
    Kilobits = "Kilobits"
    Megabits = "Megabits"
    Gigabits = "Gigabits"
    Terabits = "Terabits"
    Percent = "Percent"
    Count = "Count"
    Bytes_per_Second = "Bytes/Second"
    Kilobytes_per_Second = "Kilobytes/Second"
    Megabytes_per_Second = "Megabytes/Second"
    Gigabytes_per_Second = "Gigabytes/Second"
    Terabytes_per_Second = "Terabytes/Second"
    Bits_per_Second = "Bits/Second"
    Kilobits_per_Second = "Kilobits/Second"
    Megabits_per_Second = "Megabits/Second"
    Gigabits_per_Second = "Gigabits/Second"
    Terabits_per_Second = "Terabits/Second"
    Count_per_Second = "Count/Second"


@dataclass
class AWSCloudWatchMetricDatum:
    """
    AWS Cloudwatch MetricData struct.
    """

    metric_name: str
    value: t.Optional[float] = None
    dimensions: t.Optional[t.Dict[str, str]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    values: t.Optional[t.List[float]] = None
    counts: t.Optional[t.List[int]] = None
    unit: t.Optional[AWSCloudWatchUnit] = field(default=None)

    def to_dict(self) -> t.Dict:
        result: t.Dict[str, t.Any] = {
            "MetricName": self.metric_name,
        }

        if self.timestamp:
            result["Timestamp"] = self.timestamp

        if self.value:
            result["Value"] = self.value

        if self.unit:
            result["Unit"] = self.unit.value

        if self.values:
            result["Values"] = self.values

        if self.counts:
            result["Counts"] = self.counts

        return result


class AWSCloudWatchReporter(object):
    """
    An metrics reporter that publishes the metrics to cloudwatch when called.

    For now, only timer and counters are supported because that's all you
    need to measure performance of functions.
    """

    # https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricData.html
    # TODO Something better than 'hit limit=skip'
    PUT_METRIC_DATA_VALUES_LIMIT = 150
    PUT_METRIC_PER_PUT_LIMIT = 20

    def __init__(self, namespace: str):
        self.client = boto3.client("cloudwatch")
        self.namespace = namespace

    def get_multi_value_datums(
        self,
        name: str,
        value_count_mapping: t.Mapping[t.Union[int, float], int],
        unit: AWSCloudWatchUnit,
    ) -> t.Optional[AWSCloudWatchMetricDatum]:
        """
        For reporting multiple values. Requires a dict from values ->
        recurrence_count.

        Returns a list of datums you can then report.

        eg. If you saw the following latencies, [1, 2, 2, 3, 3, 3, 4, 5, 5, 1],
        value_count_mapping would look like
        {
            1: 2,
            2: 2,
            3: 3,
            4: 1,
            5: 1
        }
        """
        if (
            not value_count_mapping
            or len(value_count_mapping) >= self.PUT_METRIC_DATA_VALUES_LIMIT
        ):
            logger.warning(
                "Skipping `AWSCloudWatchReporter.get_multi_value_datums`:  number of metric subvalues would have errored on write."
            )
            return None

        values = []
        counts = []

        for k, v in value_count_mapping.items():
            values.append(k)
            counts.append(v)

        return AWSCloudWatchMetricDatum(
            metric_name=name, values=values, counts=counts, unit=unit
        )

    def get_counter_datum(
        self,
        name: str,
        value: int,
    ) -> AWSCloudWatchMetricDatum:
        """
        For reporting counts. Returns a single datum.
        """
        return AWSCloudWatchMetricDatum(
            metric_name=name, value=value, unit=AWSCloudWatchUnit.Count
        )

    def report(self, metric_datums: t.List[AWSCloudWatchMetricDatum]):
        # Publish metric datums to cloudwatch
        if metric_datums and len(metric_datums) <= self.PUT_METRIC_PER_PUT_LIMIT:
            self._put_metric_data(self.namespace, metric_datums)
        else:
            logger.warning(
                "Skipping `AWSCloudWatchReporter.report`: number of metrics datums would have errored on write."
            )

    def _put_metric_data(
        self, namespace: str, metric_datums: t.List[AWSCloudWatchMetricDatum]
    ):

        self.client.put_metric_data(
            Namespace=namespace, MetricData=[x.to_dict() for x in metric_datums]
        )
