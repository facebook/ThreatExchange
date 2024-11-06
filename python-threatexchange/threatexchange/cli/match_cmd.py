#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Match command for parsing simple data sources against the dataset.
"""

from dataclasses import dataclass, field
import argparse
import logging
import pathlib
import typing as t
import tempfile

from threatexchange import common
from threatexchange.cli.fetch_cmd import FetchCommand
from threatexchange.cli.helpers import FlexFilesInputAction
from threatexchange.exchanges.fetch_state import FetchedSignalMetadata

from threatexchange.signal_type.index import (
    IndexMatch,
    SignalTypeIndex,
    IndexMatchUntyped,
    SignalSimilarityInfo,
    T,
)
from threatexchange.cli.exceptions import CommandError
from threatexchange.signal_type.signal_base import BytesHasher, SignalType
from threatexchange.cli.cli_config import CLISettings
from threatexchange.content_type.content_base import ContentType, RotationType
from threatexchange.content_type.photo import PhotoContent

from threatexchange.signal_type.signal_base import MatchesStr, TextHasher, FileHasher
from threatexchange.cli import command_base


TMatcher = t.Callable[[pathlib.Path], t.List[IndexMatch]]


@dataclass
class _IndexMatchWithRotation(t.Generic[T]):
    match: IndexMatchUntyped[SignalSimilarityInfo, T]
    rotation_type: t.Optional[RotationType] = field(default=None)

    def __str__(self):
        # Supposed to be without whitespace, but let's make sure
        distance_str = "".join(self.match.similarity_info.pretty_str().split())
        if self.rotation_type is None:
            return distance_str
        return f"{self.rotation_type.name} {distance_str}"


class MatchCommand(command_base.Command):
    """
    Match content to fetched signals

    Runs the given content through applicable SignalTypes, and compare it
    with previously fetched signals stored in the index files. Only
    SignalTypes supported by the CLI and your extensions can be matched,
    even if you can fetch them. Any matches will be printed to screen.

    # Input
    You can pass in data to the command in a few different ways:
    ```
    # As an input file that contains one signal
    $ threatexchange match photo my_photo.jpg

    # As stdin
    $ echo This is my cool text | threatexchange match text -

    # Inline
    $ threatexchange match text -- This is my cool text
    ```

    # Output
    The output of this command is in the following format:

    <signal type> - (<Collab Name>) <opinion category> <label1>,<label2>,...

    The category is key to understanding what you might want to do with a match.
    Here's an explanation of the categories. Opinion categories:
    * POSITIVE_CLASS:
      All contributors of this signal believe that matching content should belong
    * INVESTIGATION_SEED:
      This content needs manual investigation to confirm or fanout to find the
      content that fits the collaboration
    * DISPUTED:
      Some members have said that this signal can be used to find content
      that fits the collaboration, but others have said it matches content
      that does not belong in the collaboration.
    * NEGATIVE_CLASS:
      Members have said content that matches does not belong in the
      collaboration, matches the wrong content on their platform, or that this
      is informational content that shouldn't be treated the same as
      POSITIVE_CLASS content.
    """

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: argparse.ArgumentParser) -> None:
        ap.add_argument(
            "content_type",
            **common.argparse_choices_pre_type_kwargs(
                [c.get_name() for c in settings.get_all_content_types()],
                settings.get_content_type,
            ),
            help="what kind of content to match",
        )

        ap.add_argument(
            "--only-signal",
            "-S",
            **common.argparse_choices_pre_type_kwargs(
                [s.get_name() for s in settings.get_all_signal_types()],
                settings.get_signal_type,
            ),
            help="limit to this signal type",
        )

        ap.add_argument(
            "--hashes",
            "-H",
            action="store_true",
            help=("force input to be interpreted as signals for the given signal type"),
        )

        ap.add_argument(
            "files",
            nargs=argparse.REMAINDER,
            action=FlexFilesInputAction,
            help="list of files or -- to interpret remainder as a string",
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
        ap.add_argument(
            "--all",
            "-A",
            action="store_true",
            help="show all matches, not just one per collaboration",
        )
        ap.add_argument(
            "--rotations",
            "-R",
            action="store_true",
            help="for photos, generate and match all 8 simple rotations",
        )

    def __init__(
        self,
        content_type: t.Type[ContentType],
        only_signal: t.Optional[t.Type[SignalType]],
        hashes: bool,
        files: t.List[pathlib.Path],
        show_false_positives: bool,
        hide_disputed: bool,
        all: bool,
        rotations: bool = False,
    ) -> None:
        self.content_type = content_type
        self.only_signal = only_signal
        self.as_hashes = hashes
        self.show_false_positives = show_false_positives
        self.hide_disputed = hide_disputed
        self.files = files
        self.all = all
        self.rotations = rotations

        if only_signal and content_type not in only_signal.get_content_types():
            raise CommandError(
                f"{only_signal.get_name()} does not "
                f"apply to {content_type.get_name()}",
                2,
            )

        if self.rotations and not issubclass(content_type, PhotoContent):
            raise CommandError(
                "--rotations flag is only available for Photo content type", 2
            )

    def execute(self, settings: CLISettings) -> None:
        if not settings.index.list():
            if not settings.in_demo_mode:
                raise CommandError("No indices available. Do you need to fetch?")
            self.stderr("You haven't built any indices, so we'll call `fetch` for you!")
            FetchCommand().execute(settings)

        signal_types = settings.get_signal_types_for_content(self.content_type)

        if self.only_signal:
            signal_types = [self.only_signal]
        types: t.Tuple[type, ...] = (FileHasher, MatchesStr)
        if self.as_hashes:
            types = (BytesHasher, TextHasher, FileHasher)
        signal_types = [s for s in signal_types if issubclass(s, types)]
        if self.as_hashes and len(signal_types) > 1:
            raise CommandError(
                f"Error: '{self.content_type.get_name()}' supports more than one SignalType."
                " for '--hashes' also use '--only-signal' to specify one of "
                f"{[s.get_name() for s in signal_types]}",
                2,
            )

        logging.info(
            "Signal types that apply: %s",
            ", ".join(s.get_name() for s in signal_types) or "None!",
        )

        indices: t.List[t.Tuple[t.Type[SignalType], SignalTypeIndex]] = []
        for s_type in signal_types:
            index = settings.index.load(s_type)
            if index is None:
                logging.info("No index for %s, skipping", s_type.get_name())
                continue
            indices.append((s_type, index))

        if not indices:
            self.stderr("No data to match against")
            return

        for path in self.files:
            for s_type, index in indices:
                seen = set()  # TODO - maybe take the highest certainty?
                if self.as_hashes:
                    results: t.Sequence[_IndexMatchWithRotation] = _match_hashes(
                        path, s_type, index
                    )
                else:
                    results = _match_file(path, s_type, index, rotations=self.rotations)

                for r in results:
                    metadatas: t.List[t.Tuple[str, FetchedSignalMetadata]] = (
                        r.match.metadata
                    )
                    distance_str = str(r)

                    for collab, fetched_data in metadatas:
                        if not self.all and collab in seen:
                            continue
                        seen.add(collab)

                        print(
                            s_type.get_name(),
                            distance_str,
                            f"({collab})",
                            fetched_data,
                        )


def _match_file(
    path: pathlib.Path,
    s_type: t.Type[SignalType],
    index: SignalTypeIndex,
    rotations: bool = False,
) -> t.Sequence[_IndexMatchWithRotation]:
    if issubclass(s_type, MatchesStr):
        matches = index.query(path.read_text())
        return [_IndexMatchWithRotation(match=match) for match in matches]

    assert issubclass(s_type, FileHasher)

    if not rotations:
        matches = index.query(s_type.hash_from_file(path))
        return [_IndexMatchWithRotation(match=match) for match in matches]

    # Handle rotations for photos
    with open(path, "rb") as f:
        image_data = f.read()

    rotated_images: t.Dict[RotationType, bytes] = PhotoContent.all_simple_rotations(
        image_data
    )
    all_matches = []

    for rotation_type, rotated_bytes in rotated_images.items():
        # Create a temporary file to hold the image bytes
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(rotated_bytes)
            temp_file_path = pathlib.Path(temp_file.name)
            matches = index.query(s_type.hash_from_file(temp_file_path))

        # Add rotation information if any matches were found
        matches_with_rotations = []
        for match in matches:
            matches_with_rotations.append(
                _IndexMatchWithRotation(match=match, rotation_type=rotation_type)
            )

        all_matches.extend(matches_with_rotations)

    return all_matches


def _match_hashes(
    path: pathlib.Path, s_type: t.Type[SignalType], index: SignalTypeIndex
) -> t.Sequence[_IndexMatchWithRotation]:
    ret: t.List[_IndexMatchWithRotation] = []
    for hash in path.read_text().splitlines():
        hash = hash.strip()
        if not hash:
            continue
        try:
            hash = s_type.validate_signal_str(hash)
        except Exception:
            logging.exception("%s failed verification on %s", s_type.get_name(), hash)
            hash_repr = repr(hash)
            if len(hash_repr) > 50:
                hash_repr = hash_repr[:47] + "..."
            raise CommandError(
                f"{hash_repr} from {path} is not a valid hash for {s_type.get_name()}",
                2,
            )
        matches = index.query(hash)
        ret.extend([_IndexMatchWithRotation(match=match) for match in matches])
    return ret
