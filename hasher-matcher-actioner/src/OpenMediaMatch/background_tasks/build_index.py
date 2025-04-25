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
    if idx_checkpoint == bank_checkpoint:
        logger.info("%s index up to date, no build needed", for_signal_type.get_name())
        return
    logger.info(
        "Building index for %s (%d signals)",
        for_signal_type.get_name(),
        0 if bank_checkpoint is None else bank_checkpoint.total_hash_count,
    )
    index_cls = for_signal_type.get_index_cls()
    signal_list = []
    last_cs = None
    content_type_counts = {}
    
    # Get the bank name from the first item to update counts later
    first_item = next(bank_store.bank_yield_content(for_signal_type), None)
    if first_item is None:
        logger.info("No content found for signal type %s", for_signal_type.get_name())
        return
        
    bank_name = first_item.bank_name
    signal_list.append((first_item.signal_val, first_item.bank_content_id))
    content_type_counts[first_item.signal_type_name] = content_type_counts.get(first_item.signal_type_name, 0) + 1
    
    # Process remaining items
    for last_cs in bank_store.bank_yield_content(for_signal_type):
        tuple = (last_cs.signal_val, last_cs.bank_content_id)
        signal_list.append(tuple)
        # Update content type counts
        content_type = last_cs.signal_type_name
        content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1
    
    built_index = index_cls.build(signal_list)
    checkpoint = SignalTypeIndexBuildCheckpoint.get_empty()
    if last_cs is not None:
        checkpoint = SignalTypeIndexBuildCheckpoint(
            last_item_timestamp=last_cs.bank_content_timestamp,
            last_item_id=last_cs.bank_content_id,
            total_hash_count=len(signal_list),
        )
    
    # Update content type counts in the bank
    if content_type_counts:
        bank = bank_store._get_bank(bank_name)
        if bank:
            # Merge with existing counts if any
            existing_counts = bank.content_type_counts or {}
            merged_counts = {**existing_counts, **content_type_counts}
            bank.content_type_counts = merged_counts
            bank_store.db.session.commit()
    
    logger.info(
        "Indexed %d signals for %s - %s",
        len(signal_list),
        for_signal_type.get_name(),
        duration_to_human_str(int(time.time() - start)),
    )
    index_store.store_signal_type_index(for_signal_type, built_index, checkpoint)
