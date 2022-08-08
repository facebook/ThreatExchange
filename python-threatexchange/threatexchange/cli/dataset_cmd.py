# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from argparse import ArgumentParser
import collections
import csv
import sys
import typing as t
import logging
from threatexchange.cli.exceptions import CommandError


from threatexchange.signal_type.signal_base import SignalType
from threatexchange.cli.cli_config import CLISettings
from threatexchange.content_type.content_base import ContentType
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.fetch_state import FetchedSignalMetadata

from threatexchange.cli import command_base
from threatexchange import common


class DatasetCommand(command_base.Command):
    """
    Introspect fetched data.

    Can print out contents in simple formats
    (ideal for sending to another system), or regenerate
    index files (ideal if distributing indices for some reason)

    Example commands:

    ```
    # Show total size of known signals
    $ threatexchange dataset

    # Show the size of one collaboration
    $ threatexchange dataset -c 'Sample Data'

    # Generate a simple CSV file for one collaboration for ease of distribution
    $ threatexchange dataset -c 'Sample Data' -P --csv > collab.csv
    ```
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
            action="store_true",
            help="print summary in terms of signals (default action)",
        )
        actions.add_argument(
            "--print-signals",
            "-P",
            action="store_true",
            help="print signals to screen",
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
            metavar="SIGNAL_TYPE",
            help="only use signals of this type",
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
            metavar="CONTENT_TYPE",
            help="only use signals for these content types",
        )
        ap.add_argument(
            "--print-zeroes",
            "-z",
            action="store_true",
            help="[--signal-summary] print counts of 0",
        )
        ap.add_argument(
            "--only-collabs",
            "-c",
            nargs="+",
            default=[],
            metavar="NAME",
            help="[-S|-P] only use items with this tag",
        )
        ap.add_argument(
            "--only-tags",
            "-t",
            nargs="+",
            default=[],
            metavar="STR",
            help="[-S|-P] only use items with these tags",
        )
        csv_mutual_group = ap.add_mutually_exclusive_group()
        csv_mutual_group.add_argument(
            "--print-signals-only",
            "-S",
            action="store_true",
            help="[-P] print type and signal only, no metadata",
        )
        csv_mutual_group.add_argument(
            "--csv",
            action="store_true",
            help="[-P] print in csv format (including header)",
        )

    def __init__(
        # These all have defaults to make it easier to call
        # only for rebuild
        self,
        # Mode
        clear_indices: bool = False,
        rebuild_indices: bool = False,
        signal_summary: bool = False,
        print_signals: bool = False,
        # Signal selectors
        only_collabs: t.Sequence[str] = (),
        only_signals: t.Sequence[t.Type[SignalType]] = (),
        only_content: t.Sequence[t.Type[ContentType]] = (),
        only_tags: t.Sequence[str] = (),
        # Print stuff
        print_zeroes: bool = False,
        print_signals_only: bool = False,
        csv: bool = False,
    ) -> None:
        self.clear_indices = clear_indices
        self.rebuild_indices = rebuild_indices
        self.print_signals = print_signals
        self.signal_summary = signal_summary or not (
            print_signals or rebuild_indices or clear_indices
        )

        self.only_collabs = set(only_collabs)
        self.only_signals = set(only_signals)
        self.only_content = set(only_content)
        self.only_tags = set(only_tags)

        self.print_zeroes = print_zeroes
        self.print_signals_only = print_signals_only
        self.csv = csv

    def execute(self, settings: CLISettings) -> None:
        if settings.fetched_state.empty():
            if not settings.in_demo_mode:
                raise CommandError("No stored state available. Do you need to fetch?")
            # FetchCommand currently imports dataset for index build, so inline for circular import
            from threatexchange.cli.fetch_cmd import FetchCommand

            self.stderr("You haven't fetched any state, so we'll call `fetch` for you!")
            FetchCommand().execute(settings)
        # Maybe consider subcommands?
        if self.clear_indices:
            self.execute_clear_indices(settings)
        elif self.rebuild_indices:
            self.execute_generate_indices(settings)
        elif self.print_signals:
            self.execute_print_signals(settings)
        else:
            assert self.signal_summary
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
        collabs = [c for c in settings.get_all_collabs() if c.enabled]
        if self.only_collabs:
            collabs = [c for c in collabs if c.name in self.only_collabs]
        return collabs

    def get_signals(
        self, settings: CLISettings, signal_types: t.Iterable[t.Type[SignalType]]
    ) -> t.Dict[
        t.Type[SignalType], t.Dict[str, t.List[t.Tuple[str, FetchedSignalMetadata]]]
    ]:
        """
        Get signals grouped by type => hash => collab name: metadata
        """
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
                store = settings.fetched_state.get_for_collab(collabs_for_store[0])
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
        for s_name, count in sorted(by_type.items(), key=lambda i: (-i[1], i[0])):
            if count or self.print_zeroes:
                print(f"{s_name}: {count}")

    def execute_print_signals(self, settings):
        signals = self.get_signals(settings, self.get_signal_types(settings))

        print_fn = self._print_stdout
        if self.csv:
            csv_writer = csv.DictWriter(
                sys.stdout, ["signal_type", "signal_str", "collab", "category", "tags"]
            )
            csv_writer.writeheader()
            print_fn = lambda *args: self._print_csv(csv_writer, *args)

        for signal_type, per_signal in signals.items():
            for signal_str, collab_signals in per_signal.items():
                if self.print_signals_only:
                    print_fn("", signal_type, signal_str, None)
                    continue
                for collab_name, metadata in collab_signals:
                    print_fn(collab_name, signal_type, signal_str, metadata)

    def execute_clear_indices(self, settings: CLISettings) -> None:
        only_signals = None
        if self.only_signals or self.only_content:
            only_signals = self.get_signal_types(settings)
        settings.index.clear(only_signals)

    def execute_generate_indices(self, settings: CLISettings) -> None:
        signal_types = self.get_signal_types(settings)

        for s_type in signal_types:
            index_cls = s_type.get_index_cls()
            signal_by_type = self.get_signals(settings, [s_type])
            signals = signal_by_type.get(s_type, {})
            if not signals:
                logging.info("No signals for %s", s_type.__name__)
                settings.index.clear([s_type])
                continue

            self.stderr(
                "Building index for",
                s_type.get_name(),
                f"with {len(signals)} signals...",
            )
            index = index_cls.build(signals.items())
            settings.index.store(s_type, index)
            self.stderr(f"Index for {s_type.get_name()} ready")

    def _print_stdout(
        self,
        collab_name: str,
        signal_type: SignalType,
        signal_str: str,
        metadata: t.Optional[FetchedSignalMetadata],
    ) -> None:
        if len(self.only_signals) != 1:
            print(signal_type.get_name(), end=" ")

        print(signal_str, end="")

        if not self.print_signals_only:
            if len(self.only_collabs) != 1:
                print("", repr(collab_name), end="")
            print("", metadata, end="")
        print()  # Complete line

    def _print_csv(
        self,
        csvwriter: csv.DictWriter,
        collab_name: str,
        signal_type: SignalType,
        signal_str: str,
        metadata: t.Optional[FetchedSignalMetadata],
    ) -> None:
        assert metadata is not None
        agg = metadata.get_as_aggregate_opinion()
        csvwriter.writerow(
            {
                "signal_type": signal_type.get_name(),
                "signal_str": signal_str,
                "collab": collab_name,
                "category": agg.category.name,
                "tags": " ".join(agg.tags),
            }
        )
