#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Hash command to convert content into signatures.
"""

import argparse
import pathlib
import typing as t
import tempfile
from pathlib import Path

from threatexchange import common
from threatexchange.cli.cli_config import CLISettings
from threatexchange.cli.exceptions import CommandError
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.file import FileContent
from threatexchange.content_type.content_base import RotationType

from threatexchange.signal_type.signal_base import FileHasher, SignalType
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

        content_choices = sorted(s.get_name() for s in settings.get_all_content_types())
        signal_choices = sorted(
            s.get_name() for s in signal_types if issubclass(s, FileHasher)
        )

        ap.add_argument(
            "content_type",
            **common.argparse_choices_pre_type_kwargs(
                choices=content_choices,
                type=settings.get_content_type,
            ),
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
            **common.argparse_choices_pre_type_kwargs(
                choices=signal_choices,
                type=settings.get_signal_type,
            ),
            help="only generate these signal types",
        )

        ap.add_argument(
            "--photo-preprocess",
            choices=["unletterbox", "rotations"],
            help=(
                "Apply one of the preprocessing steps to the image before hashing. "
                "'unletterbox' removes black borders, and 'rotations' generates all 8 "
                "simple rotations."
            ),
        )

        ap.add_argument(
            "--black-threshold",
            type=int,
            default=15,
            help=(
                "Set the black threshold for unletterboxing (default: 15)."
                "Only applies when 'unletterbox' is selected in --preprocess."
            ),
        )

        ap.add_argument(
            "--save-preprocess",
            action="store_true",
            help="save the preprocessed image data as new files",
        )

    def __init__(
        self,
        content_type: t.Type[ContentType],
        signal_type: t.Optional[t.Type[SignalType]],
        files: t.List[pathlib.Path],
        photo_preprocess: t.Optional[str] = None,
        black_threshold: int = 0,
        save_preprocess: bool = False,
    ) -> None:
        self.content_type = content_type
        self.signal_type = signal_type
        self.photo_preprocess = photo_preprocess
        self.black_threshold = black_threshold
        self.save_preprocess = save_preprocess
        self.files = files
        if self.photo_preprocess and not issubclass(self.content_type, PhotoContent):
            raise CommandError(
                "--photo-preprocess flag is only available for Photo content type", 2
            )
        if issubclass(self.content_type, FileContent):
            try:
                # Use the first file to determine content type
                self.content_type = FileContent.map_to_content_type(self.files[0])
            except ValueError as e:
                raise CommandError(f"{e}", returncode=2)

    def execute(self, settings: CLISettings) -> None:
        hashers = [
            s
            for s in settings.get_signal_types_for_content(self.content_type)
            if issubclass(s, FileHasher)
        ]
        if self.signal_type is not None:
            if self.signal_type not in hashers:
                raise CommandError.user(
                    f"{self.signal_type.get_name()} "
                    f"does not apply to {self.content_type.get_name()}"
                )

            hashers = [self.signal_type]  # type: ignore  # can't detect intersection types

        if not self.photo_preprocess:
            for file in self.files:
                for hasher in hashers:
                    hash_str = hasher.hash_from_file(file)
                    if hash_str:
                        print(hasher.get_name(), hash_str)
            return

        def pre_processed_files() -> (
            t.Iterator[t.Tuple[Path, bytes, t.Union[None, RotationType], str]]
        ):
            """
            Generator that yields preprocessed files and their metadata.
            Each item is a tuple of (file path, processed bytes, rotation name, image format).
            """
            for file in self.files:
                image_format = file.suffix.lower().lstrip(".")
                if self.photo_preprocess == "unletterbox":
                    processed_bytes = PhotoContent.unletterbox(
                        file, self.black_threshold
                    )
                    yield file, processed_bytes, None, image_format
                elif self.photo_preprocess == "rotations":
                    with open(file, "rb") as f:
                        image_bytes = f.read()
                    rotations = PhotoContent.all_simple_rotations(image_bytes)
                    for rotation_type, processed_bytes in rotations.items():
                        yield file, processed_bytes, rotation_type, image_format

        for (
            file,
            processed_bytes,
            rotation_type,
            image_format,
        ) in pre_processed_files():
            output_extension = f".{image_format.lower()}" if image_format else ".png"
            with tempfile.NamedTemporaryFile(
                delete=not self.save_preprocess, suffix=output_extension
            ) as temp_file:
                temp_file.write(processed_bytes)
                temp_file_path = Path(temp_file.name)
                for hasher in hashers:
                    hash_str = hasher.hash_from_file(temp_file_path)
                    if hash_str:
                        prefix = rotation_type.name if rotation_type else ""
                        print(f"{prefix} {hasher.get_name()} {hash_str}")
                if self.save_preprocess:
                    suffix = (
                        f"_{rotation_type.name}" if rotation_type else "_unletterboxed"
                    )
                    output_path = file.with_stem(f"{file.stem}{suffix}").with_suffix(
                        output_extension
                    )
                    temp_file_path.rename(output_path)
                    print(f"Processed image saved to: {output_path}")
