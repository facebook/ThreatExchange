# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from argparse import ArgumentParser, ArgumentTypeError
import logging
import typing as t
from threatexchange.fetcher.fetch_state import SignalOpinion, SignalOpinionCategory


from threatexchange.signal_type.signal_base import MatchesStr, SignalType, TextHasher

from threatexchange import common
from threatexchange.cli.cli_config import CLISettings
from threatexchange.content_type.content_base import ContentType
from threatexchange.fetcher.collab_config import CollaborationConfigBase
from threatexchange.cli import command_base


class LabelCommand(command_base.Command):
    """
    Label signals and content for sharing.

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
      $ threatexchange label "Sample Collab" text
    """

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: ArgumentParser) -> None:
        label_with = ap.add_mutually_exclusive_group()
        label_with.add_argument(
            "--tags",
            type=lambda s: set(s.strip().split(",")),
            metavar="CSV",
            default=set(),
            help="tags to apply to item",
        )

        label_with.add_argument(
            "--seen",
            action="store_true",
            help="tags to apply to item",
        )

        label_with.add_argument(
            "--false-positive",
            action="store_true",
            help="tags to apply to item",
        )

        label_with.add_argument(
            "--true-positive",
            action="store_true",
            help="tags to apply to item",
        )

        ap.add_argument(
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

        ap.add_argument(
            "--is-hash",
            "-H",
            action="store_true",
            help="interpret content as a hash (requires a single -S)",
        )

        ap.add_argument(
            "collab",
            type=lambda n: settings.get_collab(n),
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
            "content",
            help="the content you are labeling",
        )

    def __init__(
        self,
        content_type: t.Type[ContentType],
        content: str,
        is_hash: bool,
        collab: CollaborationConfigBase,
        only_signals: t.List[t.Type[SignalType]],
        tags: t.Set[str],
        true_positive: bool,
        false_positive: bool,
        seen: bool,
    ) -> None:
        self.collab = collab
        self.content_type = content_type
        self.content = content
        self.tags = tags
        self.only_signals = only_signals
        self.is_hash = is_hash

        if is_hash:
            if len(self.only_signals) != 1:
                raise ArgumentTypeError("[-H] use only one argument for -S")

        self.action = self.execute_upload
        if true_positive:
            self.action = self.execute_true_positive
        elif false_positive:
            self.action = self.execute_false_positive
        elif seen:
            self.action = self.execute_seen

    def execute(self, settings: CLISettings) -> None:
        self.action(settings)

    def execute_upload(self, settings: CLISettings) -> None:
        api = settings.get_api_for_collab(self.collab)
        signal_types = self.only_signals or settings.get_signal_types_for_content(
            self.content_type
        )

        if self.is_hash:
            hash_val = signal_types[0].validate_signal_str(self.content)
            api.report_opinion(
                self.collab,
                signal_types[0],
                hash_val,
                SignalOpinion(
                    api.get_own_owner_id(self.collab),
                    SignalOpinionCategory.TRUE_POSITIVE,
                    self.tags,
                ),
            )
        raise NotImplementedError

    def execute_seen(self, settings: CLISettings) -> None:
        raise NotImplementedError

    def execute_true_positive(self, settings: CLISettings) -> None:
        raise NotImplementedError

    def execute_false_positive(self, settings: CLISettings) -> None:
        raise NotImplementedError
