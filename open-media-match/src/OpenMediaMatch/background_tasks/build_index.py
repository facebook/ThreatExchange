# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import typing as t

from flask import Flask

from threatexchange.signal_type.signal_base import SignalType

from OpenMediaMatch.background_tasks.development import get_apscheduler
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.storage.interface import (
    ISignalTypeIndexStore,
    ISignalTypeConfigStore,
    IBankStore,
)

logger = logging.getLogger(__name__)


def apscheduler_build_all_indices() -> None:
    with get_apscheduler().app.app_context():
        storage = get_storage()
        build_all_indices(storage, storage, storage)


def build_all_indices(
    signal_type_cfgs: ISignalTypeConfigStore,
    bank_store: IBankStore,
    index_store: ISignalTypeIndexStore,
) -> None:
    """
    Build all indices from scratch from current bank contents and persist them

    Any additional indices (for disabled SignalTypes) are deleted.
    """
    logger.info("Running the %s background task", build_all_indices.__name__)
    enabled = signal_type_cfgs.get_enabled_signal_types()
    for st in enabled.values():
        build_index(st, bank_store, index_store)

    logger.info("Completed %s background task", build_all_indices.__name__)
    # TODO cleanup disabled / deleted signal types


def build_index(
    for_signal_type: t.Type[SignalType],
    bank_store: IBankStore,
    index_store: ISignalTypeIndexStore,
) -> None:
    """
    Build one index from scratch with the current bank contents and persist it.
    """
    logger.info("Building index for %s", for_signal_type.get_name())
    index_cls = for_signal_type.get_index_cls()
    signal_list = []
    for batch in bank_store.bank_yield_content(for_signal_type):
        for signal, bc_id in batch:
            if signal:
                tuple = (signal, bc_id)
                signal_list.append(tuple)
    logger.info(
        "Indexed %d signals for %s", len(signal_list), for_signal_type.get_name()
    )
    index_store.store_signal_type_index(for_signal_type, index_cls.build(signal_list))
