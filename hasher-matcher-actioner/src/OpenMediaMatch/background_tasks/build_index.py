# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import time
import typing as t

from threatexchange.signal_type.signal_base import SignalType

from OpenMediaMatch.background_tasks.development import get_apscheduler
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.storage.interface import (
    ISignalTypeIndexStore,
    ISignalTypeConfigStore,
    IBankStore,
    SignalTypeIndexBuildCheckpoint,
)
from OpenMediaMatch.utils.time_utils import duration_to_human_str

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
    start = time.time()
    logger.info("Running the %s background task", build_all_indices.__name__)
    enabled = signal_type_cfgs.get_enabled_signal_types()
    for st in enabled.values():
        build_index(st, bank_store, index_store)

    logger.info(
        "Completed %s background task - %s",
        build_all_indices.__name__,
        duration_to_human_str(int(time.time() - start)),
    )
    # TODO cleanup disabled / deleted signal types


def build_index(
    for_signal_type: t.Type[SignalType],
    bank_store: IBankStore,
    index_store: ISignalTypeIndexStore,
) -> None:
    """
    Build one index from scratch with the current bank contents and persist it.
    """
    start = time.time()
    # First check to see if new signals have appeared since the last build
    idx_checkpoint = index_store.get_last_index_build_checkpoint(for_signal_type)
    bank_checkpoint = bank_store.get_current_index_build_target(for_signal_type)
    if idx_checkpoint is None:
        logger.info(
            "No index found for %s, building new index", for_signal_type.get_name()
        )
    elif bank_checkpoint is None:
        logger.info(
            "No bank content found for %s, skipping index build",
            for_signal_type.get_name(),
        )
        return
    elif (
        idx_checkpoint.last_item_timestamp == bank_checkpoint.last_item_timestamp
        and idx_checkpoint.last_item_id == bank_checkpoint.last_item_id
    ):
        logger.info("%s index up to date, no build needed", for_signal_type.get_name())
        return

    logger.info(
        "Building index for %s (%d signals)",
        for_signal_type.get_name(),
        bank_checkpoint.total_hash_count,
    )
    index_cls = for_signal_type.get_index_cls()
    signal_list = []
    last_cs = None
    bank_content_counts: dict[str, dict[str, int]] = {}
    seen_signals = set()

    for last_cs in bank_store.bank_yield_content(for_signal_type):
        signal_tuple = (last_cs.signal_val, last_cs.bank_content_id)
        if signal_tuple not in seen_signals:
            signal_list.append(signal_tuple)
            seen_signals.add(signal_tuple)
            # Update content type counts for the bank
            bank = bank_store.get_bank(last_cs.bank_name)
            if bank:
                if bank.name not in bank_content_counts:
                    bank_content_counts[bank.name] = {}
                bank_content_counts[bank.name][last_cs.signal_type_name] = (
                    bank_content_counts[bank.name].get(last_cs.signal_type_name, 0) + 1
                )

    if not signal_list:
        logger.info(
            "No content found for signal type %s, creating empty index",
            for_signal_type.get_name(),
        )
        # Create an empty index with an empty checkpoint
        built_index = index_cls.build([])
        checkpoint = SignalTypeIndexBuildCheckpoint.get_empty()
        index_store.store_signal_type_index(for_signal_type, built_index, checkpoint)
        return

    built_index = index_cls.build(signal_list)
    checkpoint = SignalTypeIndexBuildCheckpoint.get_empty()
    if last_cs is not None:
        checkpoint = SignalTypeIndexBuildCheckpoint(
            last_item_timestamp=last_cs.bank_content_timestamp,
            last_item_id=last_cs.bank_content_id,
            total_hash_count=len(signal_list),
        )

    # Update content type counts in each bank
    for bank_name, counts in bank_content_counts.items():
        bank = bank_store.get_bank(bank_name)
        logger.info("Updating bank %s with counts %s", bank_name, counts)
        if bank:
            # Merge with existing counts if any
            existing_counts = bank.content_type_counts or {}
            merged_counts = {**existing_counts, **counts}
            # Update the bank with new counts
            bank.content_type_counts = merged_counts
            bank_store.bank_update(bank)

    index_store.store_signal_type_index(for_signal_type, built_index, checkpoint)
    logger.info(
        "Built index for %s in %s with %d content types",
        for_signal_type.get_name(),
        duration_to_human_str(int(time.time() - start)),
        len(bank_content_counts),
    )
