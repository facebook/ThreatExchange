# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Helpers for fetch benchmarking and testing.

In the long term, these are generic enough that should probably live in 
python-threatexchange, but for short-term needs we're just working on them 
here.
"""
from dataclasses import dataclass
import typing as t

from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    FetchedSignalMetadata,
    FetchDelta,
    SignalOpinion,
)
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.signal_exchange_api import SignalExchangeAPI
from threatexchange.signal_type.signal_base import SignalType


@dataclass
class InfiniteRandomExchangeCollabConfig(CollaborationConfigBase):
    # How many items to return per fetch_iter()
    items_per_fetch_iter: int = 500
    # How many items to return before claiming no more records
    # A limit of -1 means unlimited
    items_per_fetch: int = -1
    # How many items to return before no more records are returned
    # A limit of -1 means unlimited
    total_item_limit: int = 1000000


@dataclass
class InfiniteRandomExchangeCheckpoint(FetchCheckpointBase):
    total_fetched = 0


class InfiniteRandomExchange(
    SignalExchangeAPI[
        InfiniteRandomExchangeCollabConfig,
        InfiniteRandomExchangeCheckpoint,
        FetchedSignalMetadata,
        int,
        None,
    ]
):
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
        fetched: t.Mapping[int, None],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, FetchedSignalMetadata]]:
        ret = {}
        # TODO
        return ret

    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[InfiniteRandomExchangeCheckpoint],
    ) -> t.Iterator[FetchDelta[int, None, InfiniteRandomExchangeCheckpoint]]:
        total_fetched = 0 if checkpoint is None else checkpoint.total_fetched
        inf = float("inf")
        limit = inf
        if self.config.items_per_fetch != -1:
            limit = total_fetched + self.config.items_per_fetch
        if self.config.total_item_limit != -1:
            limit = min(limit, self.config.total_item_limit)
        while total_fetched < limit:
            new_tot = total_fetched + self.config.items_per_fetch_iter
            if limit < inf:
                new_tot = min(new_tot, int(limit))
            ret = {i: None for i in range(total_fetched, new_tot)}
            yield FetchDelta(
                ret, InfiniteRandomExchangeCheckpoint(total_fetched=new_tot)
            )
            total_fetched = new_tot
