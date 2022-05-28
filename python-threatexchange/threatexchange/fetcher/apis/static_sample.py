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

TypedDelta = SimpleFetchDelta[state.FetchCheckpointBase, state.FetchedSignalMetadata]


class StaticSampleSignalExchangeAPI(
    SignalExchangeAPI[
        CollaborationConfigBase,
        state.FetchCheckpointBase,
        state.FetchedSignalMetadata,
        TypedDelta,
    ]
):
    """
    Return a static set of sample data for demonstration.
    """

    @classmethod
    def get_name(cls) -> str:
        return "sample"

    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[state.TFetchCheckpoint],
    ) -> t.Iterator[TypedDelta]:
        sample_signals: t.List[
            t.Tuple[t.Tuple[str, str], state.FetchedSignalMetadata]
        ] = []
        for stype in supported_signal_types:
            sample_signals.extend(_signals(stype))

        updates: t.Dict[
            t.Tuple[str, str], t.Optional[state.FetchedSignalMetadata]
        ] = dict(sample_signals)

        yield TypedDelta(
            updates,
            state.FetchCheckpointBase(),
        )


def _signals(
    sig_cls: t.Type[SignalType],
) -> t.Iterable[t.Tuple[t.Tuple[str, str], state.FetchedSignalMetadata]]:
    sig_name = sig_cls.get_name()
    return (
        ((sig_name, s), state.FetchedSignalMetadata()) for s in sig_cls.get_examples()
    )
