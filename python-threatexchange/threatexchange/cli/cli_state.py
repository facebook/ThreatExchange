#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
A wrapper around loading and storing ThreatExchange data from files.

There are a few categories of state that this wraps:
  1. Checkpoints - state about previous fetches
  2. Collaboration Indicator Dumps - Raw output from threat_updates
  3. Index state - serializations of indexes for SignalType
"""

import pickle
import pathlib
import typing as t
import logging

from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.cli.exceptions import CommandError
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.fetch_state import (
    FetchDelta,
    FetchDeltaTyped,
)
from threatexchange.exchanges import helpers
from threatexchange.exchanges.signal_exchange_api import (
    SignalExchangeAPI,
    SignalExchangeAPIWithSimpleUpdates,
)
from threatexchange.signal_type import signal_base
from threatexchange.signal_type import index


class CliIndexStore:
    """
    Persistance layer for SignalTypeIndex objects for the cli.

    They are just stored to a file directory, with names based on their type.
    """

    FILE_EXTENSION = ".index"

    def __init__(self, indice_dir: pathlib.Path) -> None:
        self.dir = indice_dir

    def list(self) -> t.List[str]:
        """Return the names (SignalType.get_name()) of stored indices"""
        return [
            str(f)[: -len(self.FILE_EXTENSION)]
            for f in self.dir.glob(f"*{self.FILE_EXTENSION}")
        ]

    def clear(
        self, only_types: t.Optional[t.Iterable[t.Type[SignalType]]] = None
    ) -> None:
        """Clear persisted indices"""
        only_names = None
        if only_types is not None:
            only_names = {st.get_name() for st in only_types}
        for file in self.dir.glob(f"*{self.FILE_EXTENSION}"):
            if (
                only_names is None
                or str(file)[: -len(self.FILE_EXTENSION)] in only_names
            ):
                logging.info("Removing index %s", file)
                file.unlink()

    def _index_file(self, signal_type: t.Type[signal_base.SignalType]) -> pathlib.Path:
        """The expected path for the index for a signal type"""
        return self.dir / f"{signal_type.get_name()}{self.FILE_EXTENSION}"

    def store(
        self, signal_type: t.Type[signal_base.SignalType], index: SignalTypeIndex
    ) -> None:
        """Persist a SignalTypeIndex to disk"""
        assert signal_type.get_index_cls() == index.__class__
        path = self._index_file(signal_type)
        with path.open("wb") as fout:
            index.serialize(fout)

    def load(
        self, signal_type: t.Type[signal_base.SignalType]
    ) -> t.Optional[index.SignalTypeIndex]:
        """Load the SignalTypeIndex for this type from disk"""
        path = self._index_file(signal_type)
        if not path.exists():
            return None
        with path.open("rb") as fin:
            return signal_type.get_index_cls().deserialize(fin)


class CliSimpleState(helpers.SimpleFetchedStateStore):
    """
    A simple on-disk storage format for the CLI.

    Ideally, it should be easy to read manually (for debugging),
    but compact enough to handle very large sets of data.
    """

    def __init__(
        self, api_cls: t.Type[SignalExchangeAPI], fetched_state_dir: pathlib.Path
    ) -> None:
        super().__init__(api_cls)
        self.dir = fetched_state_dir

    def collab_file(self, collab_name: str) -> pathlib.Path:
        """The file location for collaboration state"""
        return self.dir / f"{collab_name}.state.pickle"

    def exists(self, collab: CollaborationConfigBase) -> bool:
        """
        Returns true if the state file is available

        This usually means that state is available, but the file could also be
        corrupt or unparsable.
        """
        return self.collab_file(collab.name).is_file()

    def clear(self, collab: CollaborationConfigBase) -> None:
        """Delete a collaboration and its state directory"""
        super().clear(collab)
        file = self.collab_file(collab.name)
        if file.is_file():
            logging.info("Removing %s", file)
            file.unlink(missing_ok=True)
        if file.parent.is_dir():
            if next(file.parent.iterdir(), None) is None:
                logging.info("Removing directory %s", file.parent)
                file.parent.rmdir()

    def _read_state(
        self,
        collab_name: str,
    ) -> t.Optional[FetchDeltaTyped]:

        file = self.collab_file(collab_name)
        if not file.is_file():
            return None
        try:
            with file.open("rb") as f:
                delta = pickle.load(f)

            assert isinstance(delta, FetchDelta), "Unexpected class type?"
            delta = t.cast(FetchDeltaTyped, delta)
            assert (
                delta.checkpoint.__class__ == self.api_cls.get_checkpoint_cls()
            ), f"wrong checkpoint class stored in {file}?"

            logging.debug("Loaded %s with %d records", collab_name, len(delta.updates))
            return delta
        except Exception:
            logging.exception("Failed to read state for %s", collab_name)
            raise CommandError(
                f"Failed to read state for {collab_name}. "
                "You might have to delete it with `threatexchange fetch --clear`"
            )

    def _write_state(
        self,
        collab_name: str,
        delta: FetchDeltaTyped,
    ) -> None:
        file = self.collab_file(collab_name)
        if not file.parent.exists():
            file.parent.mkdir(parents=True)

        if issubclass(self.api_cls, SignalExchangeAPIWithSimpleUpdates):
            record_sanity_check = next(
                (record for record in delta.updates.values()),
                None,
            )

            if record_sanity_check is not None:
                assert (  # Not isinstance - we want exactly this class
                    record_sanity_check.__class__ == self.api_cls.get_record_cls()
                ), (
                    f"Record cls: want {self.api_cls.get_record_cls().__name__} "
                    f"got {record_sanity_check.__class__.__name__}"
                )
        tmpfile = file.with_name(f".{file.name}")
        with tmpfile.open("wb") as f:
            pickle.dump(delta, f)
        tmpfile.rename(file)
