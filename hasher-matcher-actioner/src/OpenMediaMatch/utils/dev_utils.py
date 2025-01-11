# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.signal_type.signal_base import SignalType, CanGenerateRandomSignal

from OpenMediaMatch import persistence
from OpenMediaMatch.storage.interface import IBank


def seed_sample() -> None:
    storage = persistence.get_storage()
    storage.exchange_update(
        CollaborationConfigBase(
            name="SEED_SAMPLE",
            api=StaticSampleSignalExchangeAPI.get_name(),
            enabled=True,
        ),
        create=True,
    )


def seed_banks_random(banks: int = 2, seeds: int = 10000) -> None:
    """
    Seed the database with a large number of banks and hashes
    It will generate n banks and put n/m hashes on each bank
    """
    storage = persistence.get_storage()

    types: list[t.Type[CanGenerateRandomSignal]] = [PdqSignal, VideoMD5Signal]

    for i in range(banks):
        # create bank
        bank = IBank(name=f"SEED_BANK_{i}", matching_enabled_ratio=1.0)
        storage.bank_update(bank, create=True)

        # Add hashes
        for i in range(seeds // banks):
            signal_type = types[i % len(types)]
            random_hash = signal_type.get_random_signal()

            storage.bank_add_content(
                bank.name, {t.cast(t.Type[SignalType], signal_type): random_hash}
            )
