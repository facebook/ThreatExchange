#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Hash command to convert content into signatures.
"""

import argparse
import pathlib
import sys
import typing as t

from ..api import ThreatExchangeAPI
from ..content_type import meta
from ..dataset import Dataset
from ..descriptor import ThreatDescriptor
from ..signal_type.signal_base import FileHasher, StrHasher, SignalType
from . import command_base, fetch


# TODO consider refactor to handle overlap with match
class HashCommand(command_base.Command):
    """
    Hash content into signatures (aka hashes).

    Reads inputs as filenames by default, or as text with --as-text.

    You can also pass in via stdin by using "-" as the input.
    """

    USE_STDIN = "-"

    @classmethod
    def init_argparse(cls, ap) -> None:

        ap.add_argument(
            "content_type",
            choices=[t.get_name() for t in meta.get_all_content_types()],
            help="what kind of content to hash",
        )

        ap.add_argument(
            "--signal-type",
            "-S",
            choices=[t.get_name() for t in meta.get_all_signal_types()],
            help="only generate these signal types",
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
        self,
        content_type: str,
        signal_type: t.Optional[str],
        as_text: bool,
        content: t.Union[t.List[str], t.TextIO],
    ) -> None:
        self.content_type = [
            c for c in meta.get_all_content_types() if c.get_name() == content_type
        ][0]
        self.signal_type = signal_type

        if content == [self.USE_STDIN]:
            content = sys.stdin
        self.input_generator = self._parse_input(content, as_text)

    def _parse_input(
        self,
        input_: t.Iterable[str],
        force_input_to_text: bool,
    ) -> t.Generator[t.Union[str, pathlib.Path], None, None]:
        for token in input_:
            token = token.rstrip()
            if force_input_to_text:
                yield token
            else:
                yield pathlib.Path(token)

    def execute(self, api: ThreatExchangeAPI, dataset: Dataset) -> None:

        all_signal_types = [
            s
            for s in self.content_type.get_signal_types()
            if self.signal_type in (None, s.get_name())
        ]

        file_hashers = [s for s in all_signal_types if issubclass(s, FileHasher)]
        str_hashers = [s for s in all_signal_types if issubclass(s, StrHasher)]

        for inp in self.input_generator:
            hash_fn = lambda s, t: s.hash_from_file(t)
            signal_types: t.List[t.Any] = file_hashers
            if isinstance(inp, str):
                hash_fn = lambda s, t: s.hash_from_str(t)
                signal_types = str_hashers

            for signal_type in signal_types:
                hash_str = hash_fn(signal_type, inp)
                if hash_str:
                    print(signal_type.get_name(), hash_str)
