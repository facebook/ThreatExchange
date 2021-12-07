# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import argparse
import collections
import csv
import sys
import typing as t

from .. import threat_updates
from ..api import ThreatExchangeAPI
from ..content_type import meta
from ..dataset import Dataset
from ..threat_updates import ThreatUpdateSerialization
from . import command_base
from .dataset.simple_serialization import CliIndicatorSerialization


class DatasetCommand(command_base.Command):
    """
    Introspect the local ThreatExchange dataset.

    Can print out contents in simple formats
    (ideal for sending to another system), or regenerate
    index files (ideal if distributing indices for some reason)
    """

    @classmethod
    def init_argparse(cls, ap) -> None:
        ap.add_argument(
            "--rebuild-indices",
            "-r",
            action="store_true",
            help="rebuild indices",
        )
        ap.add_argument(
            "--print",
            "-p",
            action="store_true",
            dest="print_records",
            help="print records to screen",
        )
        ap.add_argument(
            "--type",
            "-t",
            dest="only_type",
            metavar="STR",
            help="only process one type of indicator (eg HASH_MD5), signal (eg photo_md5), or content (eg photo); specifying a signal or content type implies '--signal-summary'",
        )
        ap.add_argument(
            "--tag",
            "-g",
            dest="only_tag",
            metavar="STR",
            help="only process a single tag; implies '--signal-summary'",
        )
        ap.add_argument(
            "--indicator-only", "-i", action="store_true", help="only print indicators"
        )
        ap.add_argument(
            "--signal-summary",
            "-s",
            action="store_true",
            help="print summary in terms of signals",
        )

    def __init__(
        self,
        rebuild_indices: bool,
        only_type: t.Optional[str],
        only_tag: t.Optional[str],
        indicator_only: bool,
        signal_summary: bool,
        print_records: bool,
    ) -> None:
        self.rebuild_indices = rebuild_indices
        self.only_type = only_type
        self.only_tag = only_tag
        self.indicator_only = indicator_only
        self.signal_summary = signal_summary
        self.print_records = print_records

    def execute(self, api: ThreatExchangeAPI, dataset: Dataset) -> None:
        stores = [
            threat_updates.ThreatUpdateFileStore(
                dataset.state_dir,
                privacy_group,
                api.app_id,
                serialization=CliIndicatorSerialization,
            )
            for privacy_group in dataset.config.privacy_groups
        ]
        indicators = {}
        for store in stores:
            indicators.update(store.load_state())

        if self.only_type:
            signal_types = []
            s_type = meta.get_signal_types_by_name().get(self.only_type)
            if s_type:
                signal_types.append(s_type)
                self.signal_summary = True

            content_type = meta.get_content_types_by_name().get(self.only_type)
            if content_type:
                signal_types.extend(content_type.get_signal_types())
                self.signal_summary = True

            indicators = {
                k: v
                for k, v in indicators.items()
                if v.indicator_type == self.only_type
                or (
                    signal_types
                    and any(
                        sig_type.indicator_applies(v.indicator_type, v.rollup.labels)
                        for sig_type in signal_types
                    )
                )
            }

        if self.only_tag:
            self.signal_summary = True
            indicators = {
                k: v for k, v in indicators.items() if self.only_tag in v.rollup.labels
            }

        if self.rebuild_indices:
            generate_cli_indices(dataset, stores)
        if self.print_records:
            self._print_records(indicators)
        elif self.signal_summary:
            self.print_signal_summary(indicators)
        else:
            self.print_summary(indicators)

    def print_summary(self, indicators: t.Dict[str, CliIndicatorSerialization]):
        by_type: t.Dict[str, int] = collections.Counter()
        for indicator in indicators.values():
            by_type[indicator.indicator_type] += 1
        for name, count in sorted(by_type.items(), key=lambda i: -i[1]):
            self.stderr(f"{name}: {count}")

    def print_signal_summary(self, indicators: t.Dict[str, CliIndicatorSerialization]):
        signal_types = meta.get_signal_types_by_name()
        by_signal: t.Dict[str, int] = collections.Counter()
        for indicator in indicators.values():
            for name, signal_type in signal_types.items():
                if signal_type.indicator_applies(
                    indicator.indicator_type, list(indicator.rollup.labels)
                ):
                    by_signal[name] += 1
        for name, count in sorted(by_signal.items(), key=lambda i: -i[1]):
            self.stderr(f"{name}: {count}")

    def _print_records(self, indicators: t.Dict[str, CliIndicatorSerialization]):
        csv_writer = csv.writer(sys.stdout)
        for indicator in indicators.values():
            if self.indicator_only:
                print(indicator.indicator)
            else:
                csv_writer.writerow(indicator.as_csv_row())


def generate_cli_indices(dataset: Dataset, indicator_stores):
    signal_types = meta.get_signal_types_by_name()
    indicators: t.Dict[str, t.List] = {name: [] for name in signal_types}
    for store in indicator_stores:
        for indicator in store.load_state().values():
            for name, signal_type in signal_types.items():
                if signal_type.indicator_applies(
                    indicator.indicator_type, indicator.rollup.labels
                ):
                    indicators[name].append(indicator)

    for name, signal_type in signal_types.items():
        index_cls = signal_type.get_index_cls()
        index = None
        indicators_for_signal = indicators[name]
        if indicators_for_signal:
            index = index_cls.build(
                (indicator.indicator_type, indicator.rollup)
                for indicator in indicators_for_signal
            )
        dataset.store_index(signal_type(), index)
