# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.exchanges.signal_exchange_api import (
    TSignalExchangeAPICls,
    TSignalExchangeAPI,
)
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    CollaborationConfigBase,
    FetchedSignalMetadata,
    TUpdateRecordKey,
)

from OpenMediaMatch.storage import interface
from OpenMediaMatch.storage.interface import SignalTypeConfig


class MockedUnifiedStore(interface.IUnifiedStore):
    """
    Provides plausible default values for all store interfaces.
    """

    banks: t.Dict[str, interface.BankConfig]

    def __init__(self) -> None:
        self.banks = {
            b.name: b
            for b in (interface.BankConfig("TEST_BANK", matching_enabled_ratio=1.0),)
        }

    def is_ready(self) -> bool:
        return True

    def get_content_type_configs(self) -> t.Mapping[str, interface.ContentTypeConfig]:
        return {
            c.get_name(): interface.ContentTypeConfig(True, c)
            for c in (PhotoContent, VideoContent)
        }

    def get_signal_type_configs(self) -> t.Mapping[str, SignalTypeConfig]:
        # Needed to bamboozle mypy into working
        s_types: t.Sequence[t.Type[SignalType]] = (PdqSignal, VideoMD5Signal)
        return {s.get_name(): interface.SignalTypeConfig(1.0, s) for s in s_types}

    def _create_or_update_signal_type_override(
        self, signal_type: str, enabled_ratio: float
    ) -> None:
        """Create or update database entry for a signal type, setting a new value."""
        raise Exception("Not implemented")

    # Index
    def get_signal_type_index(
        self, signal_type: t.Type[SignalType]
    ) -> t.Optional[SignalTypeIndex[int]]:
        return signal_type.get_index_cls().build(
            (example_signal, fake_id)
            for fake_id, example_signal in enumerate(
                set(signal_type.get_examples()), start=1
            )
        )

    def store_signal_type_index(
        self,
        signal_type: t.Type[SignalType],
        index: SignalTypeIndex,
        checkpoint: interface.SignalTypeIndexBuildCheckpoint,
    ) -> None:
        raise Exception("Not implemented")

    def get_last_index_build_checkpoint(
        self, signal_type: t.Type[SignalType]
    ) -> t.Optional[interface.SignalTypeIndexBuildCheckpoint]:
        return None

    # Exchanges
    def exchange_type_get_configs(
        self,
    ) -> t.Mapping[str, interface.SignalExchangeAPIConfig]:
        return {
            e.get_name(): interface.SignalExchangeAPIConfig(e)
            for e in (StaticSampleSignalExchangeAPI,)
        }

    def exchange_type_update(
        self, cfg: interface.SignalExchangeAPIConfig, *, create: bool = False
    ) -> None:
        raise Exception("Not implemented")

    def exchange_get_api_instance(self, api_cls_name: str) -> TSignalExchangeAPI:
        return self.exchange_type_get_configs()[api_cls_name].exchange_cls()

    def exchange_update(
        self, cfg: CollaborationConfigBase, *, create: bool = False
    ) -> None:
        raise Exception("Not implemented")

    def exchange_delete(self, name: str) -> None:
        raise Exception("Not implemented")

    def exchanges_get(self) -> t.Dict[str, CollaborationConfigBase]:
        cfg_cls = StaticSampleSignalExchangeAPI.get_config_cls()
        return {
            c.name: c
            for c in (
                cfg_cls(
                    "c-TEST", api=StaticSampleSignalExchangeAPI.get_name(), enabled=True
                ),
            )
        }

    def exchange_get_fetch_status(self, name: str) -> interface.FetchStatus:
        return interface.FetchStatus.get_default()

    def exchange_get_fetch_checkpoint(
        self, name: str
    ) -> t.Optional[FetchCheckpointBase]:
        return None

    def exchange_start_fetch(self, collab_name: str) -> None:
        return

    def exchange_complete_fetch(
        self, collab_name: str, *, is_up_to_date: bool, exception: bool
    ) -> None:
        return None

    def exchange_commit_fetch(
        self,
        collab: CollaborationConfigBase,
        old_checkpoint: t.Optional[FetchCheckpointBase],
        dat: t.Dict[str, t.Any],
        checkpoint: FetchCheckpointBase,
    ):
        pass

    def exchange_get_data(
        self,
        collab_name: str,
        key: TUpdateRecordKey,
    ) -> FetchedSignalMetadata:
        raise Exception("Not implemented")

    def get_banks(self) -> t.Mapping[str, interface.BankConfig]:
        return dict(self.banks)

    def bank_update(
        self,
        bank: interface.BankConfig,
        *,
        create: bool = False,
        rename_from: t.Optional[str] = None,
    ) -> None:
        if create:
            self.banks[bank.name] = bank
        else:
            if rename_from is not None:
                self.banks.pop(rename_from)
            self.banks[bank.name] = bank

    def bank_delete(self, name: str) -> None:
        self.banks.pop(name, None)

    def bank_content_get(
        self, id: t.Iterable[int]
    ) -> t.Sequence[interface.BankContentConfig]:
        # TODO
        raise Exception("Not implemented")

    def bank_content_update(self, val: interface.BankContentConfig) -> None:
        # TODO
        raise Exception("Not implemented")

    def bank_add_content(
        self,
        bank_name: str,
        content_signals: t.Dict[t.Type[SignalType], str],
        config: t.Optional[interface.BankContentConfig] = None,
    ) -> int:
        # TODO
        raise Exception("Not implemented")

    def bank_remove_content(self, bank_name: str, content_id: int) -> None:
        # TODO
        raise Exception("Not implemented")

    def get_current_index_build_target(
        self, signal_type: t.Type[SignalType]
    ) -> interface.SignalTypeIndexBuildCheckpoint:
        return interface.SignalTypeIndexBuildCheckpoint.get_empty()

    def bank_yield_content(
        self, signal_type: t.Optional[t.Type[SignalType]] = None, batch_size: int = 100
    ) -> t.Iterator[interface.BankContentIterationItem]:
        if signal_type in (None, PdqSignal):
            for fake_id, signal in enumerate(PdqSignal.get_examples()):
                yield interface.BankContentIterationItem(
                    signal_type_name=PdqSignal.get_name(),
                    signal_val=signal,
                    bank_content_timestamp=1,
                    bank_content_id=fake_id,
                )
        elif signal_type in (None, VideoMD5Signal):
            for fake_id, signal in enumerate(VideoMD5Signal.get_examples()):
                yield interface.BankContentIterationItem(
                    signal_type_name=VideoMD5Signal.get_name(),
                    signal_val=signal,
                    bank_content_timestamp=1,
                    bank_content_id=1000 + fake_id,
                )
