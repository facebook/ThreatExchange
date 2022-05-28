# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
The fetcher is the component that talks to external APIs to get and put signals

@see SignalExchangeAPI
"""


import os
import typing as t
from dataclasses import dataclass
from pathlib import Path
from threatexchange.fetcher.simple.state import (
    SimpleFetchDelta,
)

from threatexchange.fetcher import fetch_state as state
from threatexchange.fetcher.fetch_api import SignalExchangeAPI
from threatexchange.fetcher.collab_config import CollaborationConfigWithDefaults
from threatexchange.signal_type.signal_base import SignalType

TypedDelta = SimpleFetchDelta[state.FetchCheckpointBase, state.FetchedSignalMetadata]


@dataclass
class _FileCollaborationConfigRequiredFields:
    filename: str


@dataclass
class FileCollaborationConfig(
    CollaborationConfigWithDefaults, _FileCollaborationConfigRequiredFields
):
    signal_type: t.Optional[str] = None


class LocalFileSignalExchangeAPI(
    SignalExchangeAPI[
        FileCollaborationConfig,
        state.FetchCheckpointBase,
        state.FetchedSignalMetadata,
        TypedDelta,
    ]
):
    """
    Read simple signal files off the local disk.
    """

    @classmethod
    def get_config_class(cls) -> t.Type[FileCollaborationConfig]:
        return FileCollaborationConfig

    def fetch_iter(
        self,
        _supported_signal_types: t.Sequence[t.Type[SignalType]],
        collab: FileCollaborationConfig,
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[state.TFetchCheckpoint],
    ) -> t.Iterator[TypedDelta]:
        """Fetch the whole file"""
        path = Path(collab.filename)
        assert path.exists(), f"No such file {path}"
        assert path.is_file(), f"{path} is not a file (is it a dir?)"

        # TODO - Support things other than just one item per line
        with path.open("r") as f:
            lines = f.readlines()

        updates: t.Dict[t.Tuple[str, str], t.Optional[state.FetchedSignalMetadata]] = {}
        for line in lines:
            signal_type = collab.signal_type
            signal = line.strip()
            if signal_type is None:
                signal_type, _, signal = signal.partition(" ")
            if signal_type and signal:
                updates[signal_type, signal] = state.FetchedSignalMetadata()

        yield SimpleFetchDelta(updates, state.FetchCheckpointBase())

    def report_opinion(
        self,
        collab: FileCollaborationConfig,
        s_type: t.Type[SignalType],
        signal: str,
        opinion: state.SignalOpinion,
    ) -> None:
        if opinion.category != state.SignalOpinionCategory.TRUE_POSITIVE:
            raise NotImplementedError
        if opinion.tags:
            raise NotImplementedError
        path = Path(collab.filename)
        with path.open("rb") as f:
            f.seek(-1, os.SEEK_END)
            has_newline = f.read1(1) == b"\n"
        # Appending will overwrite previous ones, and compaction is for scrubs
        with path.open("wa") as f:
            nl = "" if has_newline else "\n"
            f.write(f"{nl}{s_type.get_name()} {signal}\n")
