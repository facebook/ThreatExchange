# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Hash command to convert content into signatures.
"""

import argparse
import pathlib
import typing as t
from threatexchange import common
from threatexchange.cli.cli_config import CLISettings
from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.md5 import VideoMD5Signal

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
            s
            for s in settings.get_all_signal_types()
            if issubclass(s, (TextHasher, BytesHasher))
        ]

        ap.add_argument(
            "content_type",
            type=common.argparse_choices_pre_type(
                [c.get_name() for c in settings.get_all_content_types()],
                settings.get_content_type,
            ),
            help="what kind of content to hash",
        )

        ap.add_argument(
            "files",
            nargs=argparse.REMAINDER,
            action=FlexFilesInputAction,
            help="list of files or -- to interpret remainder as a string",
        )

        ap.add_argument(
            "--signal-type",
            "-S",
            type=common.argparse_choices_pre_type(
                [s.get_name() for s in settings.get_all_signal_types()],
                settings.get_signal_type,
            ),
            help="only generate for this signal types",
        )

        ap.add_argument(
            "--extract-content",
            "-E",
            action="count",
            default=0,
            help="Process the content further to extract more signals. Can be repeated.",
        )

    def __init__(
        self,
        content_type: ContentType,
        signal_type: t.Optional[t.Type[SignalType]],
        files: t.List[pathlib.Path],
        extract_content: int,
    ) -> None:
        self.content_type = content_type
        self.signal_type = signal_type

        self.files = files

        self.extract_steps = extract_content
        self.hashers: t.List[t.Type[SignalType]] = []
        self.seen: t.Set[t.Tuple[t.Type[ContentType], str]] = set()

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
        if self.signal_type is None:
            all_signal_types = settings.get_all_signal_types()
        else:
            all_signal_types = [self.signal_type]
        self.hashers = [s for s in all_signal_types if issubclass(s, FileHasher)]
        self.extract(settings, self.extract_steps, self.content_type, self.files)

    def extract(
        self,
        settings: CLISettings,
        steps: int,
        content_type: ContentType,
        files: t.Sequence[pathlib.Path],
        level: int = 0,
    ) -> None:
        hashers = [h for h in self.hashers if content_type in h.get_content_types()]
        for file in files:
            if self.extract_steps:
                md5 = VideoMD5Signal.hash_from_file(file)
                k = (content_type, md5)
                if k in self.seen:
                    continue
                self.seen.add(k)
            for s_type in hashers:
                hash_str = s_type.hash_from_file(file)  # type: ignore  # mixin
                if hash_str:
                    print(f"{'  ' * level}{s_type.get_name()}", hash_str)

            if steps > 0:
                ret = content_type.extract_additional_content(
                    file, settings.get_all_content_types()
                )
                for next_content, next_files in ret.items():
                    if not next_files:
                        continue
                    print(
                        f"{'  ' * level}Extracted",
                        len(next_files),
                        next_content.get_name(),
                    )
                    self.extract(
                        settings, steps - 1, next_content, next_files, level + 1
                    )
