# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from argparse import ArgumentParser, ArgumentTypeError
import argparse
import pathlib
import typing as t
from threatexchange.cli.helpers import FlexFilesInputAction
from threatexchange.fetcher.fetch_state import SignalOpinion, SignalOpinionCategory


from threatexchange.signal_type.signal_base import MatchesStr, SignalType, TextHasher

from threatexchange import common
from threatexchange.cli.cli_config import CLISettings
from threatexchange.content_type.content_base import ContentType
from threatexchange.fetcher.collab_config import CollaborationConfigBase
from threatexchange.cli import command_base


class LabelCommand(command_base.Command):
    """
    [WIP] Label signals and content for sharing.

    Warning! This command is still under construction, and is not yet stable.
    Please open an issue at https://github.com/facebook/ThreatExchange/issues
    if you need the development team to prioritize stabilitizing it.

    There are three main types of labeling:

    1. Seen
       Marking that you've observed a match, which can help others prioritize
       review, or track cross-platform spread.
    2. True Positive / False Positive
       After you've confirmed the results of a match, contributing what that
       result is can help others priotize signals with more precision.
    3. Upload
       If you have your own curated signals, sharing them with others can
       help them find matches, and give them opportunities to label your
       signals.


    Examples:
    ```
    $ threatexchange label "Sample Collab" text -l example,foo -- Some text I'm labeling
    ```
    """

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: ArgumentParser) -> None:
        label_with = ap.add_mutually_exclusive_group()
        label_with.add_argument(
            "--labels",
            "-l",
            type=lambda s: set(s.strip().split(",")),
            metavar="CSV",
            default=set(),
            help="labels to apply to item",
        )

        label_with.add_argument(
            "--seen",
            action="store_true",
            help="mark you've seen this item",
        )

        label_with.add_argument(
            "--false-positive",
            action="store_true",
            help="mark that this doesn't belong in the collaboration",
        )

        label_with.add_argument(
            "--true-positive",
            action="store_true",
            help="mark that this does belong in the collaboration",
        )

        signal_group = ap.add_mutually_exclusive_group()

        signal_group.add_argument(
            "--only-signals",
            "-S",
            nargs="+",
            type=common.argparse_choices_pre_type(
                [s.get_name() for s in settings.get_all_signal_types()],
                settings.get_signal_type,
            ),
            default=[],
            help="limit to this signal type",
        )

        signal_group.add_argument(
            "--as-hash",
            "-H",
            metavar="SIGNAL_TYPE",
            type=common.argparse_choices_pre_type(
                [s.get_name() for s in settings.get_all_signal_types()],
                settings.get_signal_type,
            ),
            help="interpret input as a hash of this type",
        )

        ap.add_argument(
            "collab",
            type=lambda n: _collab_type(n, settings),
            help="The name of the collaboration",
        )

        ap.add_argument(
            "content_type",
            type=common.argparse_choices_pre_type(
                [c.get_name() for c in settings.get_all_content_types()],
                settings.get_content_type,
            ),
            help="the type of what you are labeling",
        )

        ap.add_argument(
            "files",
            nargs=argparse.REMAINDER,
            action=FlexFilesInputAction,
            help="list of files or -- to interpret remainder as a string",
        )

    def __init__(
        self,
        content_type: t.Type[ContentType],
        files: t.List[pathlib.Path],
        as_hash: t.Optional[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        only_signals: t.List[t.Type[SignalType]],
        labels: t.Set[str],
        true_positive: bool,
        false_positive: bool,
        seen: bool,
    ) -> None:
        self.collab = collab
        self.content_type = content_type
        self.files = files
        self.labels = labels
        self.only_signals = only_signals
        self.as_hash = as_hash

        if self.collab is None:
            raise ArgumentTypeError("No such collaboration!")

        self.action = self.execute_upload
        if true_positive:
            self.action = self.execute_true_positive
        elif false_positive:
            self.action = self.execute_false_positive
        elif seen:
            self.action = self.execute_seen

    def execute(self, settings: CLISettings) -> None:
        self.stderr("This command is not implemented yet, and most actions won't work")
        self.action(settings)

    def execute_upload(self, settings: CLISettings) -> None:
        api = settings.get_api_for_collab(self.collab)
        # signal_types = self.only_signals or settings.get_signal_types_for_content(
        #     self.content_type
        # )

        if self.as_hash is not None:
            for f in self.files:
                signal_type = self.as_hash
                hash_val = signal_type.validate_signal_str(f.read_text())
                api.report_opinion(
                    self.collab,
                    signal_type,
                    hash_val,
                    SignalOpinion(
                        api.get_own_owner_id(self.collab),
                        SignalOpinionCategory.TRUE_POSITIVE,
                        self.labels,
                    ),
                )
            return
        raise NotImplementedError

    def execute_seen(self, settings: CLISettings) -> None:
        raise NotImplementedError

    def execute_true_positive(self, settings: CLISettings) -> None:
        raise NotImplementedError

    def execute_false_positive(self, settings: CLISettings) -> None:
        raise NotImplementedError


def _collab_type(name: str, settings: CLISettings) -> CollaborationConfigBase:
    ret = settings.get_collab(name)
    if ret is None:
        raise ArgumentTypeError(f"No such collab '{name}'!")
    return ret
