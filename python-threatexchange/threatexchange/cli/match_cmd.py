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

from threatexchange.signal_type.index import IndexMatch, SignalTypeIndex
from threatexchange.cli.exceptions import CommandError
from threatexchange.signal_type.signal_base import BytesHasher, SignalType
from threatexchange.cli.cli_config import CLISettings
from threatexchange.content_type.content_base import ContentType

from threatexchange.signal_type.signal_base import MatchesStr, TextHasher, FileHasher
from threatexchange.cli import command_base


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

        if only_signal and content_type not in only_signal.get_content_types():
            raise CommandError(
                f"{only_signal.get_name()} does not "
                f"apply to {content_type.get_name()}",
                2,
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
        logging.info(
            "Signal types that apply: %s",
            ", ".join(s.get_name() for s in signal_types) or "None!",
        )

        if self.as_hashes:
            hashes_grouped_by_prefix = dict()
            # Infer the signal types from the prefixes (None is used as key for hashes with no prefix)
            for path in self.files:
                _group_hashes_by_prefix(path, settings, hashes_grouped_by_prefix)
            # Validate the SignalType and append the None prefixes to the correct SignalType
            self.validate_hashes_signal_type(hashes_grouped_by_prefix, signal_types)
            signal_types = list(hashes_grouped_by_prefix.keys())
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
                    results = _match_hashes(hashes_grouped_by_prefix[s_type], s_type, index)
                else:
                    results = _match_file(path, s_type, index)

                for r in results:
                    # TODO Improve visualisation of a single multiple hash query
                    metadatas: t.List[t.Tuple[str, FetchedSignalMetadata]] = r.metadata
                    for collab, fetched_data in metadatas:
                        if not self.all and collab in seen:
                            continue
                        seen.add(collab)
                        # Supposed to be without whitespace, but let's make sure
                        distance_str = "".join(r.similarity_info.pretty_str().split())
                        print(
                            s_type.get_name(),
                            distance_str,
                            f"({collab})",
                            fetched_data,
                        )

    def validate_hashes_signal_type(
        self,
        hashes_grouped_by_prefix: t.Dict[t.Optional[SignalType], t.Set[str]],
        signal_types: t.List[t.Type[SignalType]],
    ) -> bool:
        if (
            len(hashes_grouped_by_prefix) > 2
            and None in hashes_grouped_by_prefix.keys()
        ):
            raise CommandError(
                f"Error: Provided more than one SignalType and some hashes are missing a prefix",
                2,
            )
        if self.only_signal:
            if (
                self.only_signal not in hashes_grouped_by_prefix.keys()
                and None not in hashes_grouped_by_prefix.keys()
            ):
                raise CommandError(
                    f"Error: SignalType '{self.only_signal} was provided, but inferred more from provided hashes."
                    f"Inferred signal types: {', '.join(s_type.get_name() for s_type in hashes_grouped_by_prefix.keys() if s_type)}"
                )
        if (
            len(signal_types) > 1
            and len(hashes_grouped_by_prefix) == 1
            and None in hashes_grouped_by_prefix.keys()
        ):
            raise CommandError(
                f"Error: '{self.content_type.get_name()}' supports more than one SignalType"
                "No prefix applied to the hashes, cannot infer correct SignalType"
            )
        # As well as the above validations, also need to combine the None prefixes into the correct SignalType
        if None in hashes_grouped_by_prefix.keys():
            values = set().union(*hashes_grouped_by_prefix.values())
            keys = list(hashes_grouped_by_prefix.keys())
            keys.remove(None)
            # Based on the validations, we know that there will only be one key here or one defined in settings
            hashes_grouped_by_prefix.clear()
            if not self.only_signal:
                key = signal_types[0]
                if len(keys) > 0:
                    key = keys[0]
            else:
                key = self.only_signal
            hashes_grouped_by_prefix[key] = values


def _match_file(
    path: pathlib.Path, s_type: t.Type[SignalType], index: SignalTypeIndex
) -> t.Sequence[IndexMatch]:
    if issubclass(s_type, MatchesStr):
        return index.query(path.read_text())
    assert issubclass(s_type, FileHasher)
    return index.query(s_type.hash_from_file(path))


def _group_hashes_by_prefix(
    path: pathlib.Path,
    settings: CLISettings,
    hashes_grouped_by_prefix: t.Dict[t.Optional[SignalType], t.Set[str]],
) -> None:
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        components = line.split()
        signal_type = None
        if len(components) > 1:
            # Assume it has a prefix
            possible_type = components[0]
            hash = components[1].strip()
            try:
                signal_type = settings.get_signal_type(possible_type)
                hash = signal_type.validate_signal_str(hash)
            except KeyError:
                logging.exception("Signal type '%s' is invalid", possible_type)
                raise CommandError(f"Error attempting to infer Signal Type: '{possible_type}' is not a valid Signal Type.", 2)
            except Exception as e:
                logging.exception(
                    "%s failed verification on %s", signal_type.get_name(), hash
                )
                hash_repr = repr(hash)
                if len(hash_repr) > 50:
                    hash_repr = hash_repr[:47] + "..."
                raise CommandError(
                    f"{hash} from {path} is not a valid hash for {signal_type.get_name()}",
                    2,
                )
        else:
            # Assume it doesn't have a prefix and is a raw hash
            hash = components[0]
            # We can't validate it this point as we have no context on which signal type
        hashes = hashes_grouped_by_prefix.get(signal_type, set())
        hashes.add(hash)
        hashes_grouped_by_prefix[signal_type] = hashes


def _match_hashes(
    hashes: t.Set[str],
    s_type: t.Type[SignalType],
    index: SignalTypeIndex,
) -> t.Sequence[IndexMatch]:
    ret: t.List[IndexMatch] = []
    for hash in hashes:
        hash = hash.strip()
        if not hash:
            continue
        try:
            # Need to keep this final validation as we are yet to have validated the hashes without a prefix
            hash = s_type.validate_signal_str(hash)
        except Exception:
            logging.exception("%s failed verification on %s", s_type.get_name(), hash)
            hash_repr = repr(hash)
            if len(hash_repr) > 50:
                hash_repr = hash_repr[:47] + "..."
            raise CommandError(
                f"{hash_repr} is not a valid hash for {s_type.get_name()}",
                2,
            )
        ret.extend(index.query(hash))
    return ret
