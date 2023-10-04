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
from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    CollaborationConfigBase,
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
        return {s.get_name(): interface.SignalTypeConfig(1.0, s) for s in s_types}

    def _create_or_update_signal_type_override(
        self, signal_type: str, enabled_ratio: float
    ) -> None:
        """Create or update database entry for a signal type, setting a new value."""
        raise Exception("Not implemented")

    # Index
    def get_signal_type_index(
        self, signal_type: type[SignalType]
    ) -> t.Optional[SignalTypeIndex[int]]:
        return signal_type.get_index_cls().build(
            (example_signal, fake_id)
            for fake_id, example_signal in enumerate(
                set(signal_type.get_examples()), start=1
            )
        )

    def store_signal_type_index(
        self, signal_type: t.Type[SignalType], index: SignalTypeIndex
    ) -> None:
        raise Exception("Not implemented")

    def get_last_signal_build_timestamp(self, signal_type: str) -> t.Optional[int]:
        raise Exception("Not implemented")

    # Collabs
    def get_collaborations(self) -> t.Dict[str, CollaborationConfigBase]:
        cfg_cls = StaticSampleSignalExchangeAPI.get_config_cls()
        return {
            c.name: c
            for c in (
                cfg_cls(
                    "c-TEST", api=StaticSampleSignalExchangeAPI.get_name(), enabled=True
                ),
            )
        }

    def get_collab_fetch_checkpoint(
        self, collab: CollaborationConfigBase
    ) -> t.Optional[FetchCheckpointBase]:
        return None

    def commit_collab_fetch_data(
        self,
        collab: CollaborationConfigBase,
        dat: t.Dict[str, t.Any],
        checkpoint: FetchCheckpointBase,
    ):
        pass

    def get_collab_data(
        self,
        collab_name: str,
        key: str,
        checkpoint: FetchCheckpointBase,
    ) -> t.Any:
        return None

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

    def bank_yield_content(
        self, signal_type: t.Optional[t.Type[SignalType]] = None, batch_size: int = 100
    ) -> t.Iterator[t.Sequence[t.Tuple[t.Optional[str], int]]]:
        if signal_type == PdqSignal:
            for fake_id, signal in enumerate(PdqSignal.get_examples()):
                yield [(signal, fake_id)]
        elif signal_type == VideoMD5Signal:
            for fake_id, signal in enumerate(PdqSignal.get_examples()):
                yield [(signal, fake_id)]
        return
