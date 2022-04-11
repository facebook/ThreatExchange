#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Hash command to convert content into signatures.
"""

import pathlib
import sys
import typing as t
from threatexchange.cli.cli_config import CLISettings

from threatexchange.signal_type.signal_base import BytesHasher, FileHasher, TextHasher
from threatexchange.cli import command_base


# TODO consider refactor to handle overlap with match
class HashCommand(command_base.Command):
    """
    Hash content into signatures (aka hashes).

    Reads inputs as filenames by default, though it will attempt to read
    inline with --inline. Most useful with with content type `text`.

    You can also pass in via stdin by using "-" as the content.
    """

    USE_STDIN = "-"

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap) -> None:

        signal_types = [
            s
            for s in settings.get_all_signal_types()
            if issubclass(s, (TextHasher, BytesHasher))
        ]

        ap.add_argument(
            "content_type",
            choices={c.get_name() for s in signal_types for c in s.get_content_types()},
            help="what kind of content to hash",
        )

        ap.add_argument(
            "--signal-type",
            "-S",
            choices=[s.get_name() for s in signal_types],
            help="only generate these signal types",
        )

        ap.add_argument(
            "--inline",
            "-I",
            action="store_true",
            help="interpret content inline instead of as filenames",
        )

        ap.add_argument(
            "content",
            nargs="+",
            help="list of content or '-' for stdin",
        )

    def __init__(
        self,
        content_type: str,
        signal_type: t.Optional[str],
        inline: bool,
        content: t.Union[t.List[str], t.TextIO],
    ) -> None:
        self.content_type_str = content_type
        self.signal_type = signal_type

        if content == [self.USE_STDIN]:
            content = sys.stdin
        self.input_generator = self._parse_input(content, inline)

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

    def execute(self, settings: CLISettings) -> None:
        content_type = settings.get_content_type(self.content_type_str)

        all_signal_types = [
            s
            for s in settings.get_signal_types_for_content(content_type)
            if self.signal_type in (None, s.get_name())
        ]

        file_hashers = [s for s in all_signal_types if issubclass(s, FileHasher)]
        str_hashers = [s for s in all_signal_types if issubclass(s, TextHasher)]

        for inp in self.input_generator:
            hash_fn = lambda s, t: s.hash_from_file(t)
            signal_types: t.List[t.Any] = file_hashers
            if isinstance(inp, str):
                hash_fn = lambda s, t: s.hash_from_str(t)
                signal_types = str_hashers
            for signal_type in signal_types:
                try:
                    hash_str = hash_fn(signal_type, inp)
                    if hash_str:
                        print(signal_type.get_name(), hash_str)
                except FileNotFoundError:
                    self.stderr(
                        f"The file {inp} doesn't exist or the file path is incorrect"
                    )
