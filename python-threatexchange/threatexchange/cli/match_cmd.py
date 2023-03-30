#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Match command for parsing simple data sources against the dataset.
"""

import argparse
import logging
import pathlib
import typing as t


from threatexchange import common
from threatexchange.cli.fetch_cmd import FetchCommand
from threatexchange.cli.helpers import FlexFilesInputAction
from threatexchange.exchanges.fetch_state import FetchedSignalMetadata

from threatexchange.signal_type.index import IndexMatch
from threatexchange.cli.exceptions import CommandError
from threatexchange.signal_type.signal_base import BytesHasher, SignalType
from threatexchange.cli.cli_config import CLISettings
from threatexchange.content_type.content_base import ContentType

from threatexchange.signal_type.signal_base import MatchesStr, TextHasher, FileHasher
from threatexchange.cli import command_base
from threatexchange.matcher import matcher, file_matcher, hash_matcher


TMatcher = t.Callable[[pathlib.Path], t.List[IndexMatch]]


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

    def __init__(
        self,
        content_type: t.Type[ContentType],
        only_signal: t.Optional[t.Type[SignalType]],
        hashes: bool,
        files: t.List[pathlib.Path],
        show_false_positives: bool,
        hide_disputed: bool,
        all: bool,
    ) -> None:
        self.content_type = content_type
        self.only_signal = only_signal
        self.as_hashes = hashes
        self.show_false_positives = show_false_positives
        self.hide_disputed = hide_disputed
        self.files = files
        self.all = all

    def execute(self, settings: CLISettings) -> None:
        if self.as_hashes:
            self.matcher: matcher.Matcher = hash_matcher.HashMatcher(
                settings,
                self.content_type,
                self.only_signal,
                (BytesHasher, TextHasher, FileHasher),
            )
        else:
            self.matcher = file_matcher.FileMatcher(
                settings, self.content_type, self.only_signal, (FileHasher, MatchesStr)
            )
        if not settings.index.list():
            if not settings.in_demo_mode:
                raise CommandError("No indices available. Do you need to fetch?")
            self.stderr("You haven't built any indices, so we'll call `fetch` for you!")
            FetchCommand().execute(settings)

        for path in self.files:
            seen = set()
            if self.as_hashes:
                results = self.matcher.match(*path.read_text().splitlines())
            else:
                results = self.matcher.match(path)
            for r in results:
                metadatas: t.List[t.Tuple[str, FetchedSignalMetadata]] = r.metadata
                for collab, fetched_data in metadatas:
                    if not self.all and collab in seen:
                        continue
                    seen.add(collab)
                    # Supposed to be without whitespace, but let's make sure
                    distance_str = "".join(r.similarity_info.pretty_str().split())
                    print(
                        # s_type.get_name(),
                        distance_str,
                        f"({collab})",
                        fetched_data,
                    )
