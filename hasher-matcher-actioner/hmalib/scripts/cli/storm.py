#! /usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Storm/stress test a deployed instance of HMA

Besides deploying you will likely want a place to set off the test (ec2 instance)

Run
- Submit content matching `media`, `count` times using `submit_method`

Example usage for each submission type
```
$ hmacli storm -m "<filepath>" -c 100 -v upload
$ hmacli storm -m "<filepath>" -c 100 -v bytes
$ hmacli storm -m "<signed-url>" -c 100 -v url
$ hmacli storm -m "<bucket>:<key>" -c 100 -v s3
$ hmacli storm -m "<pdq-hash>" -c 100 -v hash
```

"""

import os
import sys
import base64
import argparse
import uuid
import datetime
import requests
import urllib3
import concurrent.futures
import functools
import socket
import typing as t

from time import perf_counter
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import hmalib.scripts.cli.command_base as base
import hmalib.scripts.common.utils as utils

# "/" does not work with react router preventing the content submission details from rendering.
# However it can be used here for easier clean up between storms that do not need the UI.
ID_SEPARATOR = "-"

# Value to incorperate into content_id as an attempt to get greater prefix optimizations (ymmv).
# bucket_prefix_known = int(socket.gethostname()[-2:]) % 5


@functools.lru_cache(maxsize=None)
def _get_b64_contents(filepath):
    with open(filepath, "rb") as file:
        return str(base64.b64encode(file.read()), "utf-8")


class StormCommand(base.Command, base.NeedsAPIAccess):
    """
    Start a storm/stress test on a deployed HMA instance. Will trigger lambdas and cost some $$
    """

    @classmethod
    def init_argparse(cls, ap: argparse.ArgumentParser) -> None:
        ap.add_argument(
            "--media",
            "-m",
            help="Media to be submitted based on method. e.g. file path of photo to upload (upload/bytes), url, hash, or bucket:key (s3).",
            required=True,
        )
        ap.add_argument(
            "submit_method",
            choices=["upload", "bytes", "url", "s3", "hash", "sns-s3", "sns-url"],
            help="Method of submission to use in storm",
            default="upload",
        )
        ap.add_argument(
            "--count",
            "-c",
            help="Number of times to submit media.",
            default=1,
        )
        ap.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Print progress and percentile times for submission sets.",
        )
        ap.add_argument(
            "--retry",
            "-r",
            action="store_true",
            help="Have request retry (with exponential backoff) if errors are encoutered.",
        )
        ap.add_argument(
            "--sns_topic",
            help="ARN of SNS Topic to submit to, required when submit_method=[sns-s3,sns-url]",
            default="",
        )

    @classmethod
    def get_name(cls) -> str:
        """The display name of the command"""
        return "storm"

    @classmethod
    def get_help(cls) -> str:
        """The short help of the command"""
        return "run a storm/stress test"

    def __init__(
        self,
        media: str,
        submit_method: str,
        count: str,
        verbose: bool = False,
        retry: bool = False,
        sns_topic: str = "",
    ) -> None:
        self.media = media
        self.submit_method = submit_method
        self.count = int(count)
        self.verbose = verbose
        self.retry = retry
        self.sns_topic = sns_topic

        # hostnames are especially useful when storming from more than one instance.
        self.hostname = socket.gethostname()

    def execute(self, api: utils.HasherMatcherActionerAPI) -> None:
        sent_message_count = 0
        jobs = []

        execution_times = []

        if self.retry:
            retry_strategy = Retry(
                total=5,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=[
                    "GET",
                    "PUT",
                    "POST",
                ],  # Including POST as the API should not perform an insert if an error is returned
            )
            api.add_transport_adapter(HTTPAdapter(max_retries=retry_strategy))

        if self.submit_method in ["sns-s3", "sns-url"] and not self.sns_topic:
            print(
                f"submit_method: {self.submit_method} require's the sns topic arn be provided to `--sns_topic`"
            )
            sys.exit(1)
        # Need to compute script level RequestsPerSecond so that we can estimate
        # benchmark performance. For that, storing the start time every 200
        # requests and reporting the QPS between that and current.

        with concurrent.futures.ThreadPoolExecutor(max_workers=48) as executor:
            if self.verbose:
                print("Started adding tasks to executor")
            chunk_start_time_200 = perf_counter()

            while sent_message_count < self.count:
                jobs.append(
                    executor.submit(
                        self._submit,
                        api,
                    )
                )

                sent_message_count += 1
                if self.verbose:
                    print(f"{sent_message_count} requests prepared", end="\r")

            if self.verbose:
                print("\nDone adding tasks to executor")

            for i, completed_future in enumerate(concurrent.futures.as_completed(jobs)):
                execution_times.append(completed_future.result())
                if self.verbose:
                    progress_report_string = f"{i} of {self.count} sent!"

                    rps_report_string = f"Current 200 chunk has QPS of {(i % 200) / (perf_counter() - chunk_start_time_200)}"

                    # Report progress and RPS
                    print(f"{progress_report_string}! {rps_report_string}", end="\r")

                if i % 200 == 0:
                    # Reset chunk start time
                    chunk_start_time_200 = perf_counter()

        if self.verbose:
            print(f"\nSent all {self.count} submissions.")

            # Compute some beginner stats.
            execution_times = sorted(execution_times)
            print(
                f"""Percentiles in ms:
                    p75: {execution_times[int(len(execution_times)*0.75)]}
                    p95: {execution_times[int(len(execution_times)*0.95)]}
                    p99: {execution_times[int(len(execution_times)*0.99)]}
                """
            )

    def _get_submission_id(self, file_name: str = "", sep=ID_SEPARATOR):
        if file_name:
            file_name = f"-{file_name}"
        return f"storm-{self.submit_method}-{self.hostname}{sep}{datetime.date.today().isoformat()}{sep}{str(uuid.uuid4())}{file_name}"

    def _submit(
        self,
        api: utils.HasherMatcherActionerAPI,
    ) -> int:
        """
        Submit a single time (method depends on `submit_method`) and return the time it took in ms.
        """

        file_name = ""
        if self.submit_method in ["upload", "bytes"]:
            # get filename from filepath
            file_name = os.path.split(self.media)[-1]

        content_id = self._get_submission_id(file_name)
        additional_fields: t.List[str] = []

        start_time = perf_counter()
        try:
            if self.submit_method == "upload":
                with open(self.media, "rb") as file:
                    api.submit_via_upload_put_url(
                        content_id=content_id,
                        file=file,
                        additional_fields=additional_fields,
                    )
            elif self.submit_method == "bytes":
                api.submit_via_encoded_bytes(
                    content_id=content_id,
                    b64_file_contents=_get_b64_contents(self.media),
                    additional_fields=additional_fields,
                )
            elif self.submit_method == "url":
                api.submit_via_external_url(
                    content_id=content_id,
                    url=self.media,
                    additional_fields=additional_fields,
                )
            elif self.submit_method == "hash":
                api.submit_via_hash(
                    content_id=content_id,
                    signal_value=self.media,
                    additional_fields=additional_fields,
                )
            elif self.submit_method == "s3":
                bucket, key = self.media.split(":", 1)
                api.submit_via_s3_object(
                    content_id=content_id,
                    bucket_name=bucket,
                    object_key=key,
                    additional_fields=additional_fields,
                )
            elif self.submit_method == "sns-s3":
                bucket, key = self.media.split(":", 1)
                api.sns_submit_via_s3_object(
                    submit_topic_arn=self.sns_topic,
                    content_id=content_id,
                    bucket_name=bucket,
                    object_key=key,
                    additional_fields=additional_fields,
                )
            elif self.submit_method == "sns-url":
                api.sns_submit_via_external_url(
                    submit_topic_arn=self.sns_topic,
                    content_id=content_id,
                    url=self.media,
                    additional_fields=additional_fields,
                )
        # api methods call raise_for_status to check for error
        except (
            urllib3.exceptions.MaxRetryError,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException,
        ) as err:
            print("Error:", err)

        # convert seconds to miliseconds.
        return int((perf_counter() - start_time) * 1000)
