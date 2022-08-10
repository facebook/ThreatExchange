# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
A solution that allows loading signals directly from a file.

This is useful if you don't have access to an API, but still have a list of 
hashes from somewhere.
"""


import os
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

from threatexchange.exchanges import fetch_state as state
from threatexchange.exchanges.signal_exchange_api import (
    SignalExchangeAPIWithSimpleUpdates,
)
from threatexchange.exchanges.collab_config import CollaborationConfigWithDefaults
from threatexchange.signal_type.signal_base import SignalType

_TypedDelta = state.FetchDelta[
    t.Tuple[str, str],
    state.FetchedSignalMetadata,
    state.FetchCheckpointBase,
]


@dataclass
class _FileCollaborationConfigRequiredFields:
    filename: str = field(
        metadata={"help": "the absolute file path to the signal file"}
    )


@dataclass
class FileCollaborationConfig(
    CollaborationConfigWithDefaults, _FileCollaborationConfigRequiredFields
):
    signal_type: t.Optional[str] = field(
        default=None,
        metadata={
            "help": "if the file row doesn't list the signal type, interpret as this type (SignalType.get_name())",
            "metavar": "SIGNAL_TYPE",
        },
    )


@dataclass
class LocalFileSignalExchangeAPI(
    SignalExchangeAPIWithSimpleUpdates[
        FileCollaborationConfig,
        state.FetchCheckpointBase,
        state.FetchedSignalMetadata,
    ]
):
    """
    Read simple signal files off the local disk.
    """

    collab: FileCollaborationConfig

    @staticmethod
    def get_config_cls() -> t.Type[FileCollaborationConfig]:
        return FileCollaborationConfig

    @staticmethod
    def get_checkpoint_cls() -> t.Type[state.FetchCheckpointBase]:
        return state.FetchCheckpointBase

    @staticmethod
    def get_record_cls() -> t.Type[state.FetchedSignalMetadata]:
        return state.FetchedSignalMetadata

    @classmethod
    def for_collab(
        cls, collab: FileCollaborationConfig
    ) -> "LocalFileSignalExchangeAPI":
        return cls(collab)

    def fetch_iter(
        self,
        _supported_signal_types: t.Sequence[t.Type[SignalType]],
        checkpoint: t.Optional[state.TFetchCheckpoint],
    ) -> t.Iterator[_TypedDelta]:
        """Fetch the whole file"""
        path = Path(self.collab.filename)
        assert path.exists(), f"No such file {path}"
        assert path.is_file(), f"{path} is not a file (is it a dir?)"

        # TODO - Support things other than just one item per line
        with path.open("r") as f:
            lines = f.readlines()

        updates: t.Dict[t.Tuple[str, str], t.Optional[state.FetchedSignalMetadata]] = {}
        for line in lines:
            signal_type = self.collab.signal_type
            signal = line.strip()
            if signal_type is None:
                signal_type, _, signal = signal.partition(" ")
            if signal_type and signal:
                updates[signal_type, signal] = state.FetchedSignalMetadata()

        yield _TypedDelta(updates, state.FetchCheckpointBase())

    def report_opinion(
        self,
        s_type: t.Type[SignalType],
        signal: str,
        opinion: state.SignalOpinion,
    ) -> None:
        if opinion.category != state.SignalOpinionCategory.POSITIVE_CLASS:
            raise NotImplementedError
        if opinion.tags:
            raise NotImplementedError
        path = Path(self.collab.filename)
        with path.open("rb") as rf:
            rf.seek(-1, os.SEEK_END)
            has_newline = rf.read1(1) == b"\n"
        # Appending will overwrite previous ones, and compaction is for scrubs
        with path.open("wta") as wf:
            nl = "" if has_newline else "\n"
            wf.write(f"{nl}{s_type.get_name()} {signal}\n")
