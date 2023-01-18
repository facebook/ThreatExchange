#! /usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Simple stress test for a deployed instance of HMA `for_matches` endpoint for a signal hash.
Requires `ab` Apache HTTP server benchmarking tool https://httpd.apache.org/docs/2.4/programs/ab.html be installed
"""

import subprocess
import time
import typing as t

API_URL = "<api_url>"
TOKEN = "<token>"
HEADER = f"Authorization:{TOKEN}"

PATH_OF_REQUEST_BODY_FILE = "scripts/request_body_example_1.json"
MEDIA_URL = f"{API_URL}matches/for-media/"

TYPE = "pdq"
HASH = "<hash>"
MATCH_URL = f"{API_URL}matches/for-hash/?signal_value={HASH}&signal_type={TYPE}"

URL = MEDIA_URL


def run_ab_command(
    run_num: int,
    request: int = 100,
    workers: int = 20,
    headers: str = "",
    url: str = "localhost:3000",
    post_request_body: t.Optional[str] = None,
):
    cmd = ["ab"]
    if post_request_body:
        cmd.extend(
            [
                "-p",  # file with request body
                f"{post_request_body}",
                f"-T application/json",
            ],
        )
    cmd.extend(
        [
            "-k",  # keep alive
            "-q",
            f"-n {request}",
            f"-c {workers}",
            f"-H",
            f"{headers}",
            f"{url}",
        ],
    )
    out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Stared Run #:", run_num, "PID", out.pid)
    print("Using cmd: ", cmd)
    return out


def run_benchmark(
    verbose: bool = True,
    processes: int = 20,
    delay_btw_starts_in_sec: int = 10,  # we have this delay to allow the API to ramp up instead of flooding it all at once.
):
    runs = []
    for i in range(processes):
        runs.append(
            (
                i,
                run_ab_command(
                    run_num=i,
                    request=100000,
                    headers=HEADER,
                    url=URL,
                    post_request_body=PATH_OF_REQUEST_BODY_FILE,
                ),
            )
        )
        time.sleep(delay_btw_starts_in_sec)
    for i, run in runs:
        outs, errs = run.communicate()
        if verbose:
            print(outs.decode("utf-8"))
        print("Finish Run #:", i, "PID", run.pid)


if __name__ == "__main__":
    run_benchmark(processes=1)
