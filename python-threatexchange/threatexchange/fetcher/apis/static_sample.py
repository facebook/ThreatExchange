# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
The fetcher is the component that talks to external APIs to get and put signals

@see SignalExchangeAPI
"""


import typing as t

from threatexchange.signal_type.signal_base import SignalType

from threatexchange.fetcher import fetch_state as state
from threatexchange.fetcher.collab_config import CollaborationConfigBase
from threatexchange.fetcher.fetch_api import SignalExchangeAPI

from threatexchange.fetcher.simple.state import (
    SimpleFetchDelta,
)

TDelta = SimpleFetchDelta[state.FetchCheckpointBase, state.FetchedSignalMetadata]


class StaticSampleSignalExchangeAPI(
    SignalExchangeAPI[
        CollaborationConfigBase,
        state.FetchCheckpointBase,
        state.FetchedSignalMetadata,
        TDelta,
    ]
):
    """
    Return a static set of sample data for demonstration.
    """

    @classmethod
    def get_name(cls) -> str:
        return "sample"

    def fetch_once(
        self,
        supported_signal_types: t.List[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        _checkpoint: t.Optional[state.FetchCheckpointBase],
    ) -> TDelta:

        sample_signals: t.List[
            t.Tuple[t.Tuple[str, str], state.FetchedSignalMetadata]
        ] = []
        for stype in supported_signal_types:
            sample_signals.extend(_signals(stype))

        updates: t.Dict[
            t.Tuple[str, str], t.Optional[state.FetchedSignalMetadata]
        ] = dict(sample_signals)

        return TDelta(
            updates,
            state.FetchCheckpointBase(),
            done=True,
        )


def _signals(
    sig_cls: t.Type[SignalType],
) -> t.Iterable[t.Tuple[t.Tuple[str, str], state.FetchedSignalMetadata]]:
    sig_name = sig_cls.get_name()
    return (
        ((sig_name, s), state.FetchedSignalMetadata()) for s in sig_cls.get_examples()
    )
