#! /usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Soak/endurance test a deployed instance of HMA

Besides deploying you will need a place to set off the test (ec2 instance + long running tmux session)

Structure of the soak test

Initial set up (no point in a long running test if this doesn't work)
- Access to API via refresh token (+ client_id) 
- Image used has a hash that will match the systems index
- PR Configs (and associated signals) exist so match records will be created
- Action Rules (and associated actions) exist so action will send post request

Run
- Submit Content Test (done every interval=seconds)
- Sleep
- Repeat

"""

import argparse
import sys
import typing as t
import cmd
import os
import argparse
import time
import threading
import uuid
import datetime
import numpy as np
import pandas as pd
import typing as t

import hmalib.scripts.cli.command_base as base
import hmalib.scripts.common.utils as utils

from hmalib.scripts.common.client_lib import DeployedInstanceClient
from hmalib.scripts.common.listener import Listener
from hmalib.scripts.common.submitter import Submitter


class SoakCommand(base.Command, base.NeedsAPIAccess):
    """
    Start a soak test on a deployed HMA instance and submit until cancelled
    """

    @classmethod
    def init_argparse(cls, ap: argparse.ArgumentParser) -> None:
        ap.add_argument(
            "--hostname",
            help="Hostname used to listen for the actions webhooks.",
        )
        ap.add_argument(
            "--port",
            help="Port used to listen for the actioner.",
            default=8080,
        )
        ap.add_argument(
            "--batch_size",
            help="Number of images to submit in each batch.",
            default=5,
        )
        ap.add_argument(
            "--seconds_between_batches",
            help="Number of seconds between completed submission batches.",
            default=5,
        )
        ap.add_argument(
            "--auto_start",
            action="store_true",
            help="Start submitting right away.",
        )
        ap.add_argument(
            "--skip_listener",
            action="store_true",
            help="Do not use a listener at all.",
        )
        ap.add_argument(
            "--filepaths",
            action="extend",
            nargs="*",
            type=str,
            help="List of filepaths for submit use (will start each batch at the start of the list).",
        )

    @classmethod
    def get_name(cls) -> str:
        """The display name of the command"""
        return "soak"

    @classmethod
    def get_help(cls) -> str:
        """The short help of the command"""
        return "run a soak test"

    def __init__(
        self,
        hostname: str,
        port: int,
        batch_size: int,
        seconds_between_batches: int,
        auto_start: bool = False,
        skip_listener: bool = False,
        filepaths: t.List[str] = [],
    ) -> None:
        self.hostname = hostname
        self.port = int(port)
        self.batch_size = int(batch_size)
        self.seconds_between_batches = int(seconds_between_batches)
        self.auto_start = auto_start
        self.skip_listener = skip_listener
        self.filepaths = filepaths

    def execute(self, api: utils.HasherMatcherActionerAPI) -> None:
        helper = DeployedInstanceClient(api=api)
        if self.skip_listener:
            helper.set_up_test("http://httpstat.us/404")
        else:
            helper.set_up_test(f"http://{self.hostname}:{self.port}")

        submitter = Submitter(
            helper, self.batch_size, self.seconds_between_batches, self.filepaths
        )

        if self.skip_listener:
            listener = None
        else:
            listener = Listener(self.hostname, self.port)
            listener.start_listening()

        if self.auto_start:
            time.sleep(3)
            submitter.start()

        SoakShell(submitter, listener).cmdloop()

        if submitter.is_alive():
            submitter.stop()

        total_submit = submitter.get_total_submit_count()
        if listener:
            total_received = listener.get_post_request_count()
            listener.stop_listening()
            print("Submitter and listener stopped.")
            print(f"FINAL TOTAL SUBMITTED: {total_submit}")
            print(f"FINAL TOTAL POST requests received: {total_received}")
            difference = total_submit - total_received
            if difference:
                print(f"Difference of {difference} found")
            if difference > 0:
                print(
                    "If you exited before waiting on the listener, this is expect. (Warning the actioner may keep trying for a bit)"
                )
            if difference < 0:
                print(
                    f"Negative difference means more action request than submissions were received. (likely bug or multiply actions configured)"
                )
        else:
            print(f"FINAL TOTAL SUBMITTED: {total_submit}")

        if listener:
            if data := listener.get_submission_latencies():
                _generate_latency_stats(data)

        helper.clean_up_test()
        print(f"Test Run Complete. Thanks!")


class SoakShell(cmd.Cmd):
    intro = "Welcome! enter 'start' to begin submitting and 'info' to see current counts. Type help or ? to list commands.\n"
    prompt = "> "

    def __init__(self, submitter=None, listener=None):
        super(SoakShell, self).__init__()
        self.submitter = submitter
        self.listener = listener
        self.submitter_paused = False
        # Cache submitter setting so the lock can be used to pause
        if submitter:
            self._refresh_cached_submitter_settings()

    def _refresh_cached_submitter_settings(self):
        (
            self.batch_size_cache,
            self.sec_btw_batch_cache,
            self.total_submitted_cache,
        ) = self.submitter.get_current_values()

    def do_info(self, arg):
        "Get status of the test: info"
        if self.submitter_paused:
            print("Submitter is paused.")
        else:
            self._refresh_cached_submitter_settings()
        print(
            f"Submitter Settings: {self.batch_size_cache} items every {self.sec_btw_batch_cache} seconds."
        )
        print(f"TOTAL SUBMITTED: {self.total_submitted_cache}")
        if self.listener:
            print(
                f"TOTAL POST requests received: {self.listener.get_post_request_count()}"
            )

    def do_latency(self, arg):
        "Get the latency of submissions: latency"
        if self.listener:
            if data := self.listener.get_submission_latencies():
                _, _, latencies = list(zip(*data))
                latencies = np.array(latencies[-10:])
                if latencies.size:
                    print(
                        "Rough delay between submit to action request received (10 most recent)"
                    )
                    print(f"avg: {latencies.mean()} seconds")
                    return
            print("No requests received yet.")
            return
        print("No listener found.")

    def do_start(self, arg):
        "Start submitting thread: start"
        try:
            if self.submitter_paused:
                print("Submitter is paused. Use 'resume' instead of 'start'")
                return

            self._refresh_cached_submitter_settings()
            self.submitter.start()
            print("Started Submitter")
        except RuntimeError:
            if self.submitter.is_alive():
                print("Submitter has already started.")
            else:
                print(
                    "Submitter cannot be (re)started. Exit and run the script again to restart submitting."
                )

    def do_pause(self, arg):
        "Pause submitting thread: PAUSE"
        if not self.submitter.is_alive():
            print("Submitter is not running.")
            return
        if self.submitter_paused:
            print("Submitter is already paused.")
            return

        self._refresh_cached_submitter_settings()
        self.submitter._lock.acquire()
        print("Submitter Paused")
        print(f"TOTAL SUBMITTED: {self.total_submitted_cache}")

        self.submitter_paused = True

    def do_resume(self, arg):
        "Resume submitting thread: resume"
        if not self.submitter.is_alive():
            print("Submitter is not running.")
            return
        if not self.submitter_paused:
            print("Submitter is not paused.")
            return
        self.submitter._lock.release()
        print("Resuming submissions")
        self.submitter_paused = False

    def do_stop(self, arg):
        "Stop submitting thread: stop"
        if not self.submitter.is_alive():
            print("Submitter is not running.")
            return
        self.submitter.stop()
        if self.submitter_paused:
            self.submitter._lock.release()
            self.submitter_paused = False
        self._refresh_cached_submitter_settings()
        print("Stopped Submitter")
        print(f"TOTAL SUBMITTED: {self.total_submitted_cache}")

    def _valid_update(self, arg):
        if self.submitter_paused:
            print("Updates currently not supported while paused (keeps locking simple)")
            return False
        try:
            value = int(arg)
        except:
            print("value must be an int")
            return False
        if value <= 0:
            print("value must be positive")
            return False
        return True

    def do_update_batch_size(self, arg):
        "Update batch size: update_batch_size 5"
        if self._valid_update(arg):
            self.submitter.set_batch_size(int(arg))
            self.batch_size_cache = int(arg)
            print(f"Updated batch_size to {self.batch_size_cache}")

    def do_update_sec_btw_batch(self, arg):
        "Update seconds between batch submissions: update_sec_btw_batch 5"
        if self._valid_update(arg):
            self.submitter.set_seconds_between_batches(int(arg))
            self.sec_btw_batch_cache = int(arg)
            print(f"Updated seconds_between_batches to {self.sec_btw_batch_cache}")

    def _provide_wait_for_listener_option(self):
        submitted = self.submitter.get_total_submit_count()
        received = self.listener.get_post_request_count()
        if submitted - received > 0:
            cmd = input("Wait for listener to catch up before exiting? (y/N): ")
            if cmd == "y":
                submitted = self.submitter.get_total_submit_count()
                print(f"TOTAL SUBMITTED: {submitted}")
                received = self.listener.get_post_request_count()
                prev = -1
                try:
                    while submitted - received > 0:
                        if received > prev:
                            print(
                                f"\tWaiting on {submitted-received} more requests",
                                end="\r",
                            )
                            prev = received
                        received = self.listener.get_post_request_count()
                        time.sleep(3)
                except KeyboardInterrupt:
                    print("KeyboardInterrupt: Skipping wait\n")
            else:
                print("Not waiting for listener")

    def do_exit(self, arg):
        "Stop and exit: EXIT"
        if self.submitter.is_alive():
            self.submitter.stop()
            if self.submitter_paused:
                self.submitter._lock.release()
                self.submitter_paused = False
            print("Stopped Submitter")

        if self.listener:
            self._provide_wait_for_listener_option()

        print("\nClosing Shell...\n")
        return True


def _generate_latency_stats(
    data: t.List[t.Tuple[datetime.datetime, datetime.datetime, float]]
):
    timestamps, _, delays = list(zip(*data))
    times = pd.to_datetime(np.array(timestamps, dtype="datetime64[ns]"))
    df = pd.DataFrame({"times": times, "delays": delays})

    def func(x):
        a = x["delays"].mean()
        b = (x["delays"]).quantile(0.5)
        c = (x["delays"]).quantile(0.9)
        return pd.Series([a, b, c], index=["avg", "p50", "p90"])

    df.index = df.times

    df = df.groupby(pd.Grouper(freq="1min")).apply(func)
    print("Breaking down completed action's latency by time received in 1 min buckets")
    print(df)

    filename = "soak_test_timestamps.txt"
    print(f"Writing times to {filename}")
    print(f"Format: time_submitted, time_action_received, delta_in_seconds")
    with open(filename, "a") as f:  # append mode
        for record in data:
            f.write(f"{record[1].isoformat()}, {record[0].isoformat()}, {record[2]}\n")
