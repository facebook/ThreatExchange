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
from threatexchange.fetcher.collab_config import (
    CollaborationConfigBase,
    DefaultsForCollabConfigBase,
)
from threatexchange.signal_type.signal_base import SignalType


@dataclass
class FileCollaborationConfig(CollaborationConfigBase, DefaultsForCollabConfigBase):
    filename: str
    signal_type: t.Optional[str]


class LocalFileSignalExchangeAPI(SignalExchangeAPI):
    """
    Read simple signal files off the local disk.
    """

    @classmethod
    def get_config_class(cls) -> t.Type[FileCollaborationConfig]:
        return FileCollaborationConfig

    def fetch_once(  # type: ignore[override]  # fix with generics on base
        self,
        _supported_signal_types: t.List[t.Type[SignalType]],
        collab: FileCollaborationConfig,
        _checkpoint: t.Optional[state.FetchCheckpointBase],
    ) -> state.FetchDelta:
        """Fetch the whole file"""
        path = Path(collab.filename)
        assert path.exists(), f"No such file {path}"
        assert path.is_file(), f"{path} is not a file (is it a dir?)"

        # TODO - Support things other than just one item per line
        with path.open("r") as f:
            lines = f.readlines()

        updates = {}
        for line in lines:
            signal_type = collab.signal_type
            signal = line.strip()
            if signal_type is None:
                signal_type, _, signal = signal.partition(" ")
            if signal_type and signal:
                updates[signal_type, signal] = state.FetchedSignalMetadata()

        return SimpleFetchDelta(updates, state.FetchCheckpointBase(), done=True)

    def report_opinion(  # type: ignore[override]  # fix with generics on base
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
