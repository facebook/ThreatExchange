#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Match command for parsing simple data sources against the dataset.
"""

import argparse
import logging
import pathlib
import sys
import typing as t


from threatexchange import common
from threatexchange.cli.fetch_cmd import FetchCommand
from threatexchange.fetcher.fetch_state import FetchedSignalMetadata

from threatexchange.signal_type.index import IndexMatch
from threatexchange.cli.exceptions import CommandError
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.cli.cli_config import CLISettings
from threatexchange.content_type.content_base import ContentType

from threatexchange.signal_type.signal_base import MatchesStr, TextHasher, FileHasher
from threatexchange.cli import command_base


class MatchCommand(command_base.Command):
    """
    Match content to items in ThreatExchange.

    Using the dataset from the fetch command, try to match content. Not all
    content and hashing types are implemented, so it's possible that you
    can download signals, but not match them via this command. In some cases
    the implementation in this package is sub-optimal, either in completeness
    (i.e. only matching exact when near-matching is supported), or in runtime
    (i.e. using a linear implementation when a sublinear implementation exists)

    The output of this command is in the following format:

      <matched descriptor id> <signal type> <label1> <label2...>

    If tying this into your own integrity systems, if the result of this match
    is human review, you'll want to store the matched descriptor id and make
    a call to

      all_in_one label descriptor <matched descriptor id>

    with the results of that review.
    """

    USE_STDIN = "-"

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap) -> None:

        ap.add_argument(
            "content_type",
            type=common.argparse_choices_pre_type(
                [c.get_name() for c in settings.get_all_content_types()],
                settings.get_content_type,
            ),
            help="what kind of content to match",
        )

        ap.add_argument(
            "--only-signal",
            "-S",
            type=common.argparse_choices_pre_type(
                [s.get_name() for s in settings.get_all_signal_types()],
                settings.get_signal_type,
            ),
            help="limit to this signal type",
        )

        ap.add_argument(
            "--hashes",
            "-H",
            action="store_true",
            help=(
                "force input to be interpreted " "as signals for the given signal type"
            ),
        )

        ap.add_argument(
            "--inline",
            "-I",
            action="store_true",
            help=("force input to be intepreted inline instead of as files"),
        )

        ap.add_argument(
            "content",
            nargs="+",
            help=(
                "what to scan for matches. By default assumes filenames. "
                "Use '-' to read newline-separated stdin"
            ),
        )

        ap.add_argument(
            "--show-false-positives",
            action="store_true",
            help="show matches even if you've marked them false_positive",
        )

        ap.add_argument(
            "--hide-disputed",
            action="store_true",
            help="hide matches if someone has disputed them",
        )

    def __init__(
        self,
        content_type: t.Type[ContentType],
        only_signal: t.Optional[t.Type[SignalType]],
        hashes: bool,
        inline: bool,
        content: t.List[str],
        show_false_positives: bool,
        hide_disputed: bool,
    ) -> None:
        self.content_type = content_type
        self.only_signal = only_signal
        self.input_generator = self.parse_input(content, hashes, inline)
        self.inline = inline
        self.as_hashes = hashes
        self.show_false_positives = show_false_positives
        self.hide_disputed = hide_disputed

        if only_signal and content_type not in only_signal.get_content_types():
            raise CommandError(
                f"{only_signal.get_name()} does not "
                f"apply to {content_type.get_name()}",
                2,
            )

    def parse_input(
        self,
        input_: t.Iterable[str],
        input_is_hashes: bool,
        inline: bool,
        no_stderr=False,
    ) -> t.Generator[t.Union[str, pathlib.Path], None, None]:
        def interpret_token(tok: str) -> t.Union[str, pathlib.Path]:
            if inline:
                return tok
            path = pathlib.Path(token)
            if not path.is_file():
                raise CommandError(f"No such file {path}", 2)
            return path

        for token in input_:
            token = token.rstrip()
            if not no_stderr and token == self.USE_STDIN:
                yield from self.parse_input(
                    sys.stdin, input_is_hashes, inline, no_stderr=True
                )
                continue
            parsed = interpret_token(token)
            if input_is_hashes and isinstance(parsed, pathlib.Path):
                yield from self.parse_input(
                    parsed.open("r"),
                    input_is_hashes=True,
                    inline=True,
                    no_stderr=True,
                )
            else:
                yield parsed

    def execute(self, settings: CLISettings) -> None:
        if not settings.index.list():
            if not settings.in_demo_mode:
                raise CommandError("No indices available. Do you need to fetch?")
            self.stderr("You haven't built any indices, so we'll call `fetch` for you!")
            FetchCommand().execute(settings)

        signal_types = settings.get_signal_types_for_content(self.content_type)

        if self.only_signal:
            signal_types = [self.only_signal]

        if self.inline:
            signal_types = [
                s for s in signal_types if issubclass(s, (TextHasher, MatchesStr))
            ]
        else:
            signal_types = [s for s in signal_types if issubclass(s, FileHasher)]

        logging.info(
            "Signal types that apply: %s",
            ", ".join(s.get_name() for s in signal_types) or "None!",
        )

        matchers = []
        for s_type in signal_types:
            index = settings.index.load(s_type)
            if index is None:
                logging.info("No index for %s, skipping", s_type.get_name())
                continue
            query = None
            if self.inline:
                if issubclass(s_type, TextHasher):
                    query = lambda t, index=index: index.query(s_type.hash_from_str(t))  # type: ignore
                elif issubclass(s_type, MatchesStr):
                    query = lambda t, index=index: index.query(t)  # type: ignore
            else:
                query = lambda f, index=index: index.query(s_type.hash_from_file(f))  # type: ignore
            if query:
                matchers.append((s_type, query))

        if not matchers:
            self.stderr("No data to match against")
            return

        for inp in self.input_generator:
            seen = set()
            for s_type, matcher in matchers:
                results: t.List[IndexMatch] = matcher(inp)
                for r in results:
                    metadatas: t.List[t.Tuple[str, FetchedSignalMetadata]] = r.metadata
                    for collab, fetched_data in metadatas:
                        if collab in seen:
                            continue
                        seen.add(collab)
                        print(s_type.get_name(), f"- ({collab})", fetched_data)
