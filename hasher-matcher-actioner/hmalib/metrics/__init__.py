import collections
from contextlib import contextmanager
from functools import wraps
import logging
import time
import typing as t
import os

"""
Defines some wrappers which when invoked with the "correct" environment variable
will instrument functions and drop their metrics to cloudwatch.

Without the environment variables, will be a no-op.
"""

_ENABLE_PERF_MEASUREMENTS_ENVVAR = "MEASURE_PERFORMANCE"
measure_performance: bool = os.getenv(_ENABLE_PERF_MEASUREMENTS_ENVVAR, "False") in [
    "True",
    "1",
]

logger = logging.getLogger(__name__)


class lambda_with_datafiles:
    def prefix_impl(self):
        raise NotImplementedError()

    @property
    def download_datafiles(self):
        return f"{self.prefix_impl()}.download_datafiles"

    @property
    def parse_datafiles(self):
        return f"{self.prefix_impl()}.parse_datafiles"


class names:
    """
    Not a real class, just a bag of metric names. Ignore the lowercase name if
    you can. :)

    Because metric naming can have a very real impact on how dashboards are
    built, use this central location to allow easier following of conventions.

    Conventions:
    - The metric name should be of the format "{prefix}.{action}_{noun}"
    - prefixes can be dotted.
    - action and noun both should be free of special characters
    - if used as a timer, will be suffixed by "-count" and "-duration"
    """

    hma_namespace = "ThreatExchange/HMA"

    class pdq_hasher_lambda:
        _prefix = "lambdas.pdqhasher"

        download_file = f"{_prefix}.download_file"
        hash = f"{_prefix}.hash"

    class pdq_indexer_lambda(lambda_with_datafiles):
        _prefix = "lambdas.pdqindexer"

        def prefix_impl(self):
            return _prefix

        merge_datafiles = f"{_prefix}.merge_datafiles"
        build_index = f"{_prefix}.build_index"
        upload_index = f"{_prefix}.upload_index"

    class pdq_matcher_lambda:
        _prefix = "lambdas.pdqmatcher"

        download_index = f"{_prefix}.download_index"
        parse_index = f"{_prefix}.parse_index"
        search_index = f"{_prefix}.search_index"
        write_match_record = f"{_prefix}.write_match_record"

    class api_hash_count(lambda_with_datafiles):
        _prefix = "api.hashcount"

        def prefix_impl(self):
            return self._prefix

    class hasher:
        _prefix = "hasher"

        download_file = f"{_prefix}.download_file"
        write_record = f"{_prefix}.write_record"
        publish_message = f"{_prefix}.publish_message"

        @classmethod
        def hash(cls, hash_type: str):
            return f"{cls._prefix}.hash.{hash_type}"

    class indexer:
        _prefix = "indexer"

        download_datafiles = f"{_prefix}.download_datafiles"
        parse_datafiles = f"{_prefix}.parse_datafiles"
        build_index = f"{_prefix}.build_index"
        upload_index = f"{_prefix}.upload_index"
        merge_datafiles = f"{_prefix}.merge_datafiles"
        search_index = f"{_prefix}.search_index"
        download_index = f"{_prefix}.download_index"
        get_bank_data = f"{_prefix}.get_bank_data"

    class lcc:
        _prefix = "lcc"
        get_data = f"{_prefix}.get_data"
        in_memory_processing = f"{_prefix}.in_memory_processing"
        build_index = f"{_prefix}.build_index"


_METRICS_NAMESPACE_ENVVAR = "METRICS_NAMESPACE"
METRICS_NAMESPACE = os.getenv(_METRICS_NAMESPACE_ENVVAR, names.hma_namespace)

counts: collections.Counter = collections.Counter()
timers: t.Mapping[str, collections.Counter] = collections.defaultdict(
    collections.Counter
)


@contextmanager
def _no_op_timer(name):
    yield


def _no_op_flush(namespace: str = "does not matter"):
    pass


if measure_performance:
    logger.info(
        "Performance measurement requested. Supplying appmetrics instrumentation."
    )
    from hmalib.metrics.cloudwatch import AWSCloudWatchReporter, AWSCloudWatchUnit

    @contextmanager
    def _timer_wrapper(name):
        """
        While in most other setups you'd see some amount of sampling, lambdas
        are different. A single container will be used for a batches sized at
        10/100. At that, sampling will lose information. So, while we stream all
        data to cloudwatch, cloudwatch on its end will do the necessary
        statistical math to give us quantiles.

        We don't expect the lambdas to be used in multi-threaded environments.
        This impl is not guaranteed to be thread-safe.

        A timer does two things. It counts and it times. It will result in two
        metrics "{name}-duration" and "{name}-count"
        """
        count_name = f"{name}-count"
        duration_name = f"{name}-duration"

        start_ms: int = int(time.perf_counter() * 1000)

        yield

        duration_ms: int = int(time.perf_counter() * 1000) - start_ms

        timers[duration_name].update({duration_ms: 1})
        counts.update({count_name: 1})

    def _metrics_flush(namespace: str = METRICS_NAMESPACE):
        """
        Flushes metrics to an AWS Reporter.
        Warning not flush will not go through if it would hit
        PutMetricData's Limit See AWSCloudWatchReporter.PUT_METRIC_DATA_VALUES_LIMIT
        """
        try:
            reporter = AWSCloudWatchReporter(namespace)
            datums = []
            datums.extend([reporter.get_counter_datum(k, v) for k, v in counts.items()])

            for duration_name, value_count_mapping in timers.items():
                # if value_count_mapping is empty or > PUT_METRIC_DATA_VALUES_LIMIT,
                # method returns None. filter those out otherwise report will throw an error.
                if datum := reporter.get_multi_value_datums(
                    name=duration_name,
                    value_count_mapping=value_count_mapping,
                    unit=AWSCloudWatchUnit.Milliseconds,
                ):
                    datums.append(datum)

            reporter.report(datums)
        except Exception as e:
            logger.exception("Couldn't report metrics to cloudwatch")

    flush = _metrics_flush
    timer = _timer_wrapper
else:
    logger.info(
        "Performance measurement not requested. Supplying no-op instrumentation."
    )

    flush = _no_op_flush
    timer = _no_op_timer
