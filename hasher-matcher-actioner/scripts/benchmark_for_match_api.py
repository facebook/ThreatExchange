#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Simple stress test for a deployed instance of HMA `for_matches` endpoint for a signal hash.
Requires `ab` Apache HTTP server benchmarking tool https://httpd.apache.org/docs/2.4/programs/ab.html be installed
"""

import subprocess
import time

TYPE = "pdq"
HASH = "<hash>"
API_URL = "<api_url>"
TOKEN = "<token>"
URL = f"{API_URL}matches/for-hash/?signal_value={HASH}&signal_type={TYPE}"
HEADER = f"Authorization:{TOKEN}"


def run_ab_command(
    run_num: int,
    request: int = 100,
    workers: int = 20,
    headers: str = "",
    url: str = "localhost:3000",
):
    cmd = ["ab"]
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
    return out


def run_benchmark(
    verbose: bool = True,
    processes: int = 20,
    delay_btw_starts_in_sec: int = 10,  # we have this delay to allow the API to ramp up instead of flooding it all at once.
):
    runs = []
    for i in range(processes):
        runs.append(
            (i, run_ab_command(run_num=i, request=100000, headers=HEADER, url=URL))
        )
        time.sleep(delay_btw_starts_in_sec)
    for i, run in runs:
        outs, errs = run.communicate()
        if verbose:
            print(outs.decode("utf-8"))
        print("Finish Run #:", i, "PID", run.pid)


if __name__ == "__main__":
    run_benchmark(processes=10)
