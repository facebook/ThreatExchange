# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import time
import gc
import typing as t
from typing import Optional

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
    logger.info(f"Starting index build for {for_signal_type.get_name()}")

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
    
    # Use try/finally to ensure cleanup happens even on exceptions
    signal_list = []
    built_index: Optional[t.Any] = None
    last_cs = None
    signal_count = 0
    
    try:
        # Collect signals
        for last_cs in bank_store.bank_yield_content(for_signal_type):
            signal_list.append((last_cs.signal_val, last_cs.bank_content_id))
            signal_count += 1
        
        # Build index
        index_cls = for_signal_type.get_index_cls()
        built_index = index_cls.build(signal_list)
        
        # Clear signal_list early to reduce memory peak during storage
        signal_list.clear()
        
        # Create checkpoint
        checkpoint = SignalTypeIndexBuildCheckpoint.get_empty()
        if last_cs is not None:
            checkpoint = SignalTypeIndexBuildCheckpoint(
                last_item_timestamp=last_cs.bank_content_timestamp,
                last_item_id=last_cs.bank_content_id,
                total_hash_count=signal_count,
            )
            
        # Store the index
        if built_index is not None:
            index_store.store_signal_type_index(for_signal_type, built_index, checkpoint)
        
    finally:
        # Guaranteed cleanup even if exceptions occur
        # Explicitly clear large objects to help with memory management  
        if 'signal_list' in locals():
            signal_list.clear()
            del signal_list
        
        # Clear reference to built_index after storage
        if 'built_index' in locals() and built_index is not None:
            built_index = None
        
        # Force garbage collection to reclaim memory
        gc.collect()
    
    logger.info(
        "Indexed %d signals for %s - %s",
        signal_count,
        for_signal_type.get_name(),
        duration_to_human_str(int(time.time() - start)),
    )

