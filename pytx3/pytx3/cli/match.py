#!/usr/bin/env python

"""
Match command for parsing simple data sources against the dataset.
"""

import argparse
import pathlib
import sys
import typing as t

from ..content_type import meta
from ..dataset import Dataset
from ..signal_type.signal_base import FileMatcher, HashMatcher, StrMatcher
from . import command_base, fetch


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
    def init_argparse(cls, ap) -> None:

        ap.add_argument(
            "content_type",
            choices=[t.get_name() for t in meta.get_all_content_types()],
            help="what kind of content to match",
        )

        ap.add_argument(
            "--hashes",
            "-H",
            action="store_true",
            help=(
                "instead of content (i.e. videos), "
                "input contains intermediate representations (i.e. video MD5s)"
            ),
        )

        ap.add_argument(
            "--as-text",
            "-T",
            action="store_true",
            help="force input to be interpreted as text instead of as filenames",
        )

        ap.add_argument(
            "content",
            nargs="+",
            help=(
                "what to match against. Accepts filenames, "
                "quoted strings, or '-' to read newline-separated stdin"
            ),
        )

    def __init__(
        self, content_type: str, hashes: bool, as_text: bool, content: t.List[str]
    ) -> None:
        self.content_type = [
            c for c in meta.get_all_content_types() if c.get_name() == content_type
        ][0]
        self.input_generator = self.parse_input(content, hashes, as_text)
        self.as_hashes = hashes

    def parse_input(
        self,
        input_: t.Iterable[str],
        input_is_hashes: bool,
        force_input_to_text: bool,
        no_stderr=False,
    ) -> t.Generator[t.Union[str, pathlib.Path], None, None]:
        def interpret_token(
            tok: str,
        ) -> t.Generator[t.Union[str, pathlib.Path], None, None]:
            if force_input_to_text:
                return tok
            path = pathlib.Path(token)
            if path.exists():
                return path
            return tok

        for token in input_:
            token = token.rstrip()
            if not no_stderr and token == self.USE_STDIN:
                yield from self.parse_input(
                    sys.stdin, input_is_hashes, force_input_to_text, no_stderr=True
                )
                continue
            parsed = interpret_token(token)
            if input_is_hashes and isinstance(parsed, pathlib.Path):
                yield from self.parse_input(
                    parsed.open("r"),
                    input_is_hashes=True,
                    force_input_to_text=True,
                    no_stderr=True,
                )
            else:
                yield parsed

    def execute(self, dataset: Dataset) -> None:
        if dataset.is_cache_empty:
            self.stderr(
                "Looks like you are running this for the first time. Fetching some sample data."
            )
            fetch.FetchCommand(sample=True).execute(dataset)

        all_signal_types = dataset.load_cache(
            s() for s in self.content_type.get_signal_types()
        )

        file_matchers = [s for s in all_signal_types if isinstance(s, FileMatcher)]
        str_matchers = [s for s in all_signal_types if isinstance(s, StrMatcher)]

        match_str = lambda s, t: s.match(t)
        if self.as_hashes:
            match_str = lambda s, t: s.match_hash(t)
            str_matchers = [s for s in all_signal_types if isinstance(s, HashMatcher)]

        seen = set()
        for inp in self.input_generator:
            match_fn = lambda s, t: s.match_file(t)
            signal_types = file_matchers
            if isinstance(inp, str):
                match_fn = match_str
                signal_types = str_matchers

            for signal_type in signal_types:
                for match in match_fn(signal_type, inp):
                    if match.primary_descriptor_id not in seen:
                        seen.add(match.primary_descriptor_id)
                        print(
                            match.primary_descriptor_id,
                            signal_type.get_name(),
                            " ".join(
                                sorted(
                                    l
                                    for l in match.labels
                                    if l in dataset.config.labels
                                )
                            ),
                        )
