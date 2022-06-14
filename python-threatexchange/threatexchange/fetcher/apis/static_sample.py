# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Returns the hardcoded example signals from SignalType implementations.

This makes it easier to demonstrate new signal types locally, even without
access to any API.

The CLI defaults to this being the only collaboration.
"""


import typing as t

from threatexchange.signal_type.signal_base import SignalType

from threatexchange.fetcher import fetch_state as state
from threatexchange.fetcher.collab_config import CollaborationConfigBase
from threatexchange.fetcher.fetch_api import (
    SignalExchangeAPIWithSimpleUpdates,
)

_TypedDelta = state.FetchDelta[
    t.Dict[t.Tuple[str, str], t.Optional[state.FetchedSignalMetadata]],
    state.FetchCheckpointBase,
]


class StaticSampleSignalExchangeAPI(
    SignalExchangeAPIWithSimpleUpdates[
        CollaborationConfigBase,
        state.FetchCheckpointBase,
        state.FetchedSignalMetadata,
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
    ) -> t.Iterator[_TypedDelta]:
        sample_signals: t.List[
            t.Tuple[t.Tuple[str, str], state.FetchedSignalMetadata]
        ] = []
        for stype in supported_signal_types:
            sample_signals.extend(_signals(stype))

        updates: t.Dict[
            t.Tuple[str, str], t.Optional[state.FetchedSignalMetadata]
        ] = dict(sample_signals)

        yield _TypedDelta(
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
