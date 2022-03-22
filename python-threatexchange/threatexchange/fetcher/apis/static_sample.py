# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
The fetcher is the component that talks to external APIs to get and put signals

@see SignalExchangeAPI
"""


import typing as t

from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.signal_type.pdq_ocr import PdqOcrSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.raw_text import RawTextSignal
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.url import URLSignal
from threatexchange.signal_type.trend_query import TrendQuery, TrendQuerySignal

from threatexchange.fetcher import fetch_state as state
from threatexchange.fetcher.collab_config import CollaborationConfigBase
from threatexchange.fetcher.fetch_api import SignalExchangeAPI

from threatexchange.fetcher.simple.state import (
    SimpleFetchDelta,
    SimpleFetchedSignalMetadata,
)


class StaticSampleSignalExchangeAPI(SignalExchangeAPI):
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
    ) -> SimpleFetchDelta:

        sample_signals: t.List[
            t.Tuple[t.Tuple[str, str], state.FetchedSignalMetadata]
        ] = []
        for stype in supported_signal_types:
            sample_signals.extend(_signals(stype))

        return SimpleFetchDelta(
            dict(sample_signals),
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
