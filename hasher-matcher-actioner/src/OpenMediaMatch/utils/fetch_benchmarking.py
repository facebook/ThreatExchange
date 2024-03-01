# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Helpers for fetch benchmarking and testing.

In the long term, these are generic enough that should probably live in 
python-threatexchange, but for short-term needs we're just working on them 
here.
"""
from dataclasses import dataclass, field, replace
from collections import defaultdict
import time
import typing as t

from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    FetchedSignalMetadata,
    FetchDelta,
)
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.signal_exchange_api import SignalExchangeAPI
from threatexchange.signal_type.signal_base import SignalType, CanGenerateRandomSignal


@dataclass
class InfiniteRandomExchangeCollabConfig(CollaborationConfigBase):
    """
    Settings for the random signal generator API.

    Here are some useful ones for testing OMM (to paste in the UI):

    Fetch a small amount of items per fetch, which exercises delete/create
      {"new_items_per_fetch": 20, "updates_per_fetch_iter": 1, "deletes_per_fetch_iter": 1}

    PDQ loadtest (10M):
      {"total_item_limit": 10000000, "only_signal_types": ["pdq"]}
    """

    # How many items to return per fetch_iter()
    new_items_per_fetch_iter: int = 500
    # How many items to return before claiming no more records
    # A limit of -1 means unlimited
    new_items_per_fetch: int = -1
    # How many items to return before no more records are returned
    # A limit of -1 means unlimited
    total_item_limit: int = 1000000
    updates_per_fetch_iter: int = 0
    deletes_per_fetch_iter: int = 0
    # Simulate IO time
    sleep_per_iter: float = 0.0
    # Only these signal_types
    only_signal_types: t.Set[str] = field(default_factory=set)


@dataclass
class InfiniteRandomExchangeCheckpoint(FetchCheckpointBase):
    next_id: int = 0
    # Updates are on even ids starting with 0
    update_count: int = 0
    # Deletes are on odd ids starting with 1
    delete_count: int = 0

    def get_creates(
        self, signal_types: t.Sequence[t.Type[SignalType]], count: int
    ) -> dict[int, t.Tuple[str, str] | None]:
        ret = {
            i: self._get_signal(i, signal_types)
            for i in range(self.next_id, self.next_id + count)
        }
        self.next_id += count
        return ret

    def get_updates(
        self, signal_types: t.Sequence[t.Type[SignalType]], count: int
    ) -> dict[int, t.Tuple[str, str] | None]:
        ret: dict[int, t.Tuple[str, str] | None] = {
            i * 2: self._get_signal(i * 2, signal_types, is_update=True)
            for i in range(self.update_count, self.update_count + count)
        }
        self.update_count += count
        return ret

    def get_deletes(self, count: int) -> dict[int, None]:
        ret = {
            i * 2 + 1: None for i in range(self.delete_count, self.delete_count + count)
        }
        self.delete_count += count
        return ret

    def get_expected_signal(
        self, idx: int, supported: t.Sequence[t.Type[SignalType]]
    ) -> t.Type[SignalType] | None:
        """Which signal do we expect to have in this position after updating?"""
        if not supported:
            return None
        if idx % 2 == 0 and idx < self.update_count * 2:
            idx += 1
        if idx % 2 == 1 and idx < self.delete_count * 2:
            return None
        return supported[idx % len(supported)]

    @staticmethod
    def _get_signal(
        idx: int, supported: t.Sequence[t.Type[SignalType]], *, is_update: bool = False
    ) -> t.Tuple[str, str] | None:
        if not supported:
            return "", ""
        idx += int(is_update)
        st = supported[idx % len(supported)]
        return st.get_name(), t.cast(CanGenerateRandomSignal, st).get_random_signal()


class InfiniteRandomExchange(
    SignalExchangeAPI[
        InfiniteRandomExchangeCollabConfig,
        InfiniteRandomExchangeCheckpoint,
        FetchedSignalMetadata,
        int,
        t.Tuple[str, str],
    ]
):
    """
    This SignalExchangeAPI generates random hashes for e2e testing.

    By changing the config settings, it can even fetch an unbounded number
    of signals.
    """

    def __init__(self, config: InfiniteRandomExchangeCollabConfig) -> None:
        self.config = config

    @classmethod
    def for_collab(
        cls, collab: InfiniteRandomExchangeCollabConfig
    ) -> "SignalExchangeAPI":
        return cls(collab)

    @staticmethod
    def get_checkpoint_cls() -> t.Type[InfiniteRandomExchangeCheckpoint]:
        return InfiniteRandomExchangeCheckpoint

    @staticmethod
    def get_record_cls() -> t.Type[FetchedSignalMetadata]:
        return FetchedSignalMetadata

    @staticmethod
    def get_config_cls() -> t.Type[InfiniteRandomExchangeCollabConfig]:
        return InfiniteRandomExchangeCollabConfig

    @classmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        collab: InfiniteRandomExchangeCollabConfig,
        fetched: t.Mapping[int, t.Tuple[str, str]],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, FetchedSignalMetadata]]:
        if collab.only_signal_types:
            signal_types = [
                st for st in signal_types if st.get_name() in collab.only_signal_types
            ]
        st_mapping = {st.get_name(): st for st in signal_types}
        by_name: dict[str, dict[str, FetchedSignalMetadata]] = defaultdict(dict)
        for st_name, st_val in fetched.values():
            by_name[st_name][st_val] = FetchedSignalMetadata()
        ret = {}
        for st_name, signals in by_name.items():
            st = st_mapping.get(st_name)
            if st is None:
                continue
            ret[st] = signals
        return ret

    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[InfiniteRandomExchangeCheckpoint],
    ) -> t.Iterator[
        FetchDelta[int, t.Tuple[str, str], InfiniteRandomExchangeCheckpoint]
    ]:
        if self.config.only_signal_types:
            supported_signal_types = [
                st
                for st in supported_signal_types
                if st.get_name() in self.config.only_signal_types
            ]
        supported_signal_types = [
            st
            for st in supported_signal_types
            if issubclass(st, CanGenerateRandomSignal)
        ]

        next_checkpoint = replace(checkpoint or InfiniteRandomExchangeCheckpoint())
        inf = float("inf")
        limit = inf
        if self.config.new_items_per_fetch != -1:
            limit = next_checkpoint.next_id + self.config.new_items_per_fetch
        if self.config.total_item_limit != -1:
            limit = min(limit, self.config.total_item_limit)
        while next_checkpoint.next_id < limit:
            count = self.config.new_items_per_fetch_iter
            if limit < inf:
                count = min(int(limit) - next_checkpoint.next_id, count)
            ret = next_checkpoint.get_creates(supported_signal_types, count)
            if self.config.updates_per_fetch_iter:
                ret.update(
                    next_checkpoint.get_updates(
                        supported_signal_types, self.config.updates_per_fetch_iter
                    )
                )
            if self.config.deletes_per_fetch_iter:
                ret.update(
                    next_checkpoint.get_deletes(self.config.deletes_per_fetch_iter)
                )
            if self.config.sleep_per_iter > 0:
                time.sleep(self.config.sleep_per_iter)
            yield FetchDelta(
                ret,
                replace(next_checkpoint),
            )
