#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Hash command to convert content into signatures.
"""

import argparse
import pathlib
import typing as t
from threatexchange.cli.cli_config import CLISettings

from threatexchange.signal_type.signal_base import (
    BytesHasher,
    FileHasher,
    SignalType,
    TextHasher,
)
from threatexchange.cli import command_base
from threatexchange.cli.helpers import FlexFilesInputAction


class HashCommand(command_base.Command):
    """
    Take content and convert it into signatures (aka hashes)

    # Input
    You can pass in data to the command in a few different ways:
    (Note - you may not be able to hash text without an extension)
    ```
    # As an input file that contains one signal
    $ threatexchange hash photo my_photo.jpg

    # As stdin
    $ echo This is my cool text | threatexchange hash text -

    # Inline
    $ threatexchange hash text -- This is my cool text
    ```

    # Output
    <SignalType> <hash string>
    """

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: argparse.ArgumentParser) -> None:

        signal_types = [
            s for s in settings.get_all_signal_types() if issubclass(s, FileHasher)
        ]

        ap.add_argument(
            "content_type",
            choices={c.get_name() for s in signal_types for c in s.get_content_types()},
            help="what kind of content to hash",
        )

        ap.add_argument(
            "files",
            nargs=argparse.REMAINDER,
            action=FlexFilesInputAction,
            help="list of files, URLs, - for stdin, or -- to interpret remainder as a string",
        )

        ap.add_argument(
            "--signal-type",
            "-S",
            choices=[s.get_name() for s in signal_types],
            help="only generate these signal types",
        )

    def __init__(
        self,
        content_type: str,
        signal_type: t.Optional[str],
        files: t.List[pathlib.Path],
    ) -> None:
        self.content_type_str = content_type
        self.signal_type = signal_type

        self.files = files

    def execute(self, settings: CLISettings) -> None:
        content_type = settings.get_content_type(self.content_type_str)

        all_signal_types = [
            s
            for s in settings.get_signal_types_for_content(content_type)
            if self.signal_type in (None, s.get_name())
        ]
        hashers = [s for s in all_signal_types if issubclass(s, FileHasher)]

        for file in self.files:
            for hasher in hashers:
                hash_str = hasher.hash_from_file(file)
                if hash_str:
                    print(hasher.get_name(), hash_str)
