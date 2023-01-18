# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import sys
import time
import random

from hmalib.metrics import timer, names, flush
from hmalib.metrics.cloudwatch import AWSCloudWatchReporter

"""
Does not really have tests, but more of a demo. :)

Run with
$ MEASURE_PERFORMANCE=1 PYTHONPATH=. python scripts/gen_fake_cloudwatch_metrics.py
"""


def worker():
    # just spend some time
    with timer(names.pdq_hasher_lambda.download_file):
        time.sleep(random.random() / 100.0)

    with timer(names.pdq_hasher_lambda.hash):
        time.sleep(random.random() / 100.0)


def main():
    reporter = (
        AWSCloudWatchReporter(namespace="ThreatExchange/HMA-Test-Cloudwatch-Reporter"),
    )

    # emulate some work
    print("Hit CTRL-C to stop the process. Will publish metrics on being interrupted.")
    while True:
        try:
            worker()
        except KeyboardInterrupt:
            break

    flush(namespace="ThreatExchange/HMA-Test-Cloudwatch-Reporter")


if __name__ == "__main__":
    main()
