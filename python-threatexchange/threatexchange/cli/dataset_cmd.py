# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from argparse import ArgumentParser
import collections
import csv
import sys
import typing as t
import logging


from threatexchange.signal_type.signal_base import SignalType
from threatexchange import signal_type
from threatexchange.cli.cli_config import CLISettings
from threatexchange.content_type.content_base import ContentType
from threatexchange.fetcher.collab_config import CollaborationConfigBase
from threatexchange.fetcher.fetch_state import FetchedSignalMetadata

from threatexchange.cli import command_base
from threatexchange import common


class DatasetCommand(command_base.Command):
    """
    Introspect fetched data.

    Can print out contents in simple formats
    (ideal for sending to another system), or regenerate
    index files (ideal if distributing indices for some reason)
    """

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: ArgumentParser) -> None:
        actions = ap.add_mutually_exclusive_group()
        actions.add_argument(
            "--rebuild-indices",
            "-r",
            action="store_true",
            help="rebuild indices from fetched data",
        )
        actions.add_argument(
            "--clear-indices",
            "-X",
            action="store_true",
            help="clear all indices",
        )
        actions.add_argument(
            "--signal-summary",
            "-S",
            action="store_true",
            help="print summary in terms of signals",
        )
        actions.add_argument(
            "--print-records",
            "-P",
            action="store_true",
            help="print records to screen",
        )

        type_selector = ap.add_mutually_exclusive_group()
        type_selector.add_argument(
            "--only-signals",
            "-s",
            nargs="+",
            default=[],
            type=common.argparse_choices_pre_type(
                choices=[s.get_name() for s in settings.get_all_signal_types()],
                type=settings.get_signal_type,
            ),
            help="only process these sigals",
        )
        type_selector.add_argument(
            "--only-content",
            "-C",
            nargs="+",
            default=[],
            type=common.argparse_choices_pre_type(
                choices=[s.get_name() for s in settings.get_all_content_types()],
                type=settings.get_content_type,
            ),
            help="only process signals for these content types",
        )
        ap.add_argument(
            "--only-collabs",
            "-c",
            nargs="+",
            default=[],
            metavar="NAME",
            help="[-S|-P] only count items with this tag",
        )
        ap.add_argument(
            "--only-tags",
            "-t",
            default=[],
            metavar="STR",
            help="[-S|-P] only count items with these tags",
        )
        ap.add_argument(
            "--signals-only",
            "-i",
            action="store_true",
            help="[-P] only print signals",
        )
        ap.add_argument(
            "--limit",
            "-l",
            action="store_true",
            help="[-P] only print this many records",
        )

    def __init__(
        # These all have defaults to make it easier to call
        # only for rebuld
        self,
        # Mode
        clear_indices: bool = False,
        rebuild_indices: bool = False,
        signal_summary: bool = False,
        print_records: bool = False,
        # Signal selectors
        only_collabs: t.Sequence[str] = (),
        only_signals: t.Sequence[t.Type[SignalType]] = (),
        only_content: t.Sequence[t.Type[ContentType]] = (),
        only_tags: t.Sequence[str] = (),
        # Print stuff
        signals_only: bool = False,
        limit: t.Optional[int] = None,
    ) -> None:
        self.clear_indices = clear_indices
        self.rebuild_indices = rebuild_indices
        self.print_records = print_records
        self.signal_summary = signal_summary

        self.only_collabs = set(only_collabs)
        self.only_signals = set(only_signals)
        self.only_content = set(only_content)
        self.only_tags = set(only_tags)
        self.signals_only = signals_only
        self.limit = limit

    def execute(self, settings: CLISettings) -> None:
        # Maybe consider subcommands?
        if self.clear_indices:
            self.execute_clear_indices(settings)
        elif self.rebuild_indices:
            self.execute_generate_indices(settings)
        elif self.print_records:
            self.execute_print_records(settings)
        elif self.signal_summary:
            self.execute_print_signal_summary(settings)
        else:
            self.execute_print_summary(settings)

    def get_signal_types(self, settings: CLISettings) -> t.Set[t.Type[SignalType]]:
        signal_types = self.only_signals or settings.get_all_signal_types()
        if self.only_content:
            signal_types = [
                s
                for s in signal_types
                if any(c in self.only_content for c in s.get_content_types())
            ]
        return set(signal_types)

    def get_collabs(self, settings: CLISettings) -> t.List[CollaborationConfigBase]:
        collabs = [
            c for c in settings.get_all_collabs(default_to_sample=True) if c.enabled
        ]
        if self.only_collabs:
            collabs = [c for c in collabs if c.name in self.only_collabs]
        return collabs

    def get_signals(
        self, settings: CLISettings, signal_types: t.Iterable[t.Type[SignalType]]
    ) -> t.Dict[
        t.Type[SignalType], t.Dict[str, t.List[t.Tuple[str, FetchedSignalMetadata]]]
    ]:
        collabs = self.get_collabs(settings)

        collab_by_api: t.Dict[str, t.List[CollaborationConfigBase]] = {}
        for collab_config in collabs:
            collab_by_api.setdefault(collab_config.api, []).append(collab_config)
        by_type = {}
        for s_type in signal_types:
            by_signal: t.Dict[
                str,
                t.List[t.Tuple[str, FetchedSignalMetadata]],
            ] = {}
            for collabs_for_store in collab_by_api.values():
                store = settings.get_fetch_store_for_collab(collabs_for_store[0])
                by_collab = store.get_for_signal_type(collabs_for_store, s_type)
                for collab, signals in by_collab.items():
                    for signal, record in signals.items():
                        if self.only_tags:
                            for opinion in record.get_as_opinions():
                                if any(t in self.only_tags for t in opinion.tags):
                                    break
                            else:
                                continue
                        by_signal.setdefault(signal, []).append((collab, record))
            by_type[s_type] = by_signal
        return by_type

    def execute_print_summary(self, settings: CLISettings):
        signals = self.get_signals(settings, self.get_signal_types(settings))
        by_type: t.Dict[str, int] = collections.Counter()
        for s_type, type_signals in signals.items():
            by_type[s_type.get_name()] += len(type_signals)
        for s_name, count in sorted(by_type.items(), key=lambda i: -i[1]):
            self.stderr(f"{s_name}: {count}")

    def execute_print_signal_summary(self, settings):
        raise NotImplementedError
        # signal_types = meta.get_signal_types_by_name()
        # by_signal: t.Dict[str, int] = collections.Counter()
        # for indicator in indicators.values():
        #     for name, signal_type in signal_types.items():
        #         if signal_type.indicator_applies(
        #             indicator.indicator_type, list(indicator.rollup.labels)
        #         ):
        #             by_signal[name] += 1
        # for name, count in sorted(by_signal.items(), key=lambda i: -i[1]):
        #     self.stderr(f"{name}: {count}")

    def execute_print_records(self, settings):
        raise NotImplementedError
        # csv_writer = csv.writer(sys.stdout)
        # for indicator in indicators.values():
        #     if self.indicator_only:
        #         print(indicator.indicator)
        #     else:
        #         csv_writer.writerow(indicator.as_csv_row())

    def execute_clear_indices(self, settings: CLISettings) -> None:
        only_signals = None
        if self.only_signals or self.only_content:
            only_signals = self.get_signal_types(settings)
        settings.index_store.clear(only_signals)

    def execute_generate_indices(self, settings: CLISettings) -> None:
        signal_types = self.get_signal_types(settings)

        for s_type in signal_types:
            index_cls = s_type.get_index_cls()
            signal_by_type = self.get_signals(settings, [s_type])
            signals = signal_by_type.get(s_type, {})
            if not signals:
                logging.info("No signals for %s", s_type.__name__)
                settings.index_store.clear([s_type])
                continue

            self.stderr(
                "Building index for",
                s_type.get_name(),
                f"with {len(signals)} signals...",
            )
            index = index_cls.build(signals.items())
            settings.index_store.store_index(s_type, index)
            self.stderr(f"Index for {s_type.get_name()} ready")
