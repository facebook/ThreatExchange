# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.signal_base import SignalType

from OpenMediaMatch.storage import interface
from OpenMediaMatch.storage.interface import SignalTypeConfig


class MockedUnifiedStore(interface.IUnifiedStore):
    """
    Provides plausible default values for all store interfaces.
    """

    def get_content_type_configs(self) -> t.Mapping[str, interface.ContentTypeConfig]:
        return {
            c.get_name(): interface.ContentTypeConfig(True, c)
            for c in (PhotoContent, VideoContent)
        }

    def get_exchange_type_configs(self) -> t.Mapping[str, TSignalExchangeAPICls]:
        return {e.get_name(): e for e in (StaticSampleSignalExchangeAPI,)}

    def get_signal_type_configs(self) -> t.Mapping[str, SignalTypeConfig]:
        # Needed to bamboozle mypy into working
        s_types: t.Sequence[t.Type[SignalType]] = (PdqSignal, VideoMD5Signal)
        return {s.get_name(): interface.SignalTypeConfig(True, s) for s in s_types}

    def get_signal_type_index(
        self, signal_type: type[SignalType]
    ) -> t.Optional[SignalTypeIndex[int]]:
        return signal_type.get_index_cls().build(
            (example_signal, fake_id)
            for fake_id, example_signal in enumerate(
                set(signal_type.get_examples()), start=1
            )
        )
