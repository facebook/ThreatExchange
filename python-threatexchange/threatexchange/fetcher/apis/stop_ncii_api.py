# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
SignalExchangeAPI impl StopNCII.org

"""


import time
import typing as t
from dataclasses import dataclass

from threatexchange.fetcher import fetch_state as state
from threatexchange.fetcher.fetch_api import SignalExchangeAPI
from threatexchange.fetcher.collab_config import (
    CollaborationConfigBase,
)
from threatexchange.signal_type.signal_base import SignalType


@dataclass
class StopNCIICheckpoint(
    state.FetchCheckpointBase,
):
    update_time: int
    last_fetch_time: int

    def is_stale(self) -> bool:
        """Consider stale after 30d of not fetching"""
        return time.time() - self.last_fetch_time > 3600 * 24 * 30

    def get_progress_timestamp(self) -> t.Optional[int]:
        return self.update_time


class StopNCIIAPI(SignalExchangeAPI):
    def fetch_once(  # type: ignore[override]  # fix with generics on base
        self,
        supported_signal_types: t.List[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        checkpoint: t.Optional[StopNCIICheckpoint],
    ) -> state.FetchDelta:
        # TODO
        raise NotImplementedError("TODO not yet implemented")
        # now = int(time.time())
        # return SimpleFetchDelta({}, StopNCIICheckpoint(now, now, True))
