# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Returns the hardcoded example signals from SignalType implementations.

This makes it easier to demonstrate new signal types locally, even without
access to any API.

The CLI defaults to this being the only collaboration.
"""


import typing as t

from threatexchange.signal_type.signal_base import SignalType

from threatexchange.exchanges import fetch_state as state
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.signal_exchange_api import (
    SignalExchangeAPIWithSimpleUpdates,
)

_TypedDelta = state.FetchDelta[
    t.Tuple[str, str],
    state.FetchedSignalMetadata,
    state.NoCheckpointing,
]


class StaticSampleSignalExchangeAPI(
    SignalExchangeAPIWithSimpleUpdates[
        CollaborationConfigBase,
        state.NoCheckpointing,
        state.FetchedSignalMetadata,
    ]
):
    """Return a static set of sample data for demonstration"""

    @classmethod
    def get_name(cls) -> str:
        return "sample"

    @staticmethod
    def get_config_cls() -> t.Type[CollaborationConfigBase]:
        return CollaborationConfigBase

    @staticmethod
    def get_checkpoint_cls() -> t.Type[state.NoCheckpointing]:
        return state.NoCheckpointing

    @staticmethod
    def get_record_cls() -> t.Type[state.FetchedSignalMetadata]:
        return state.FetchedSignalMetadata

    @classmethod
    def for_collab(
        cls, collab: CollaborationConfigBase
    ) -> "StaticSampleSignalExchangeAPI":
        return cls()

    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
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
            state.NoCheckpointing(),
        )


def _signals(
    sig_cls: t.Type[SignalType],
) -> t.Iterable[t.Tuple[t.Tuple[str, str], state.FetchedSignalMetadata]]:
    sig_name = sig_cls.get_name()
    return (
        ((sig_name, s), state.FetchedSignalMetadata()) for s in sig_cls.get_examples()
    )
