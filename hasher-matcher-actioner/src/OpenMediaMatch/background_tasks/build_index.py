# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import multiprocessing
import os
import time
import typing as t

from threatexchange.signal_type.signal_base import SignalType

from OpenMediaMatch.background_tasks.development import get_apscheduler
from OpenMediaMatch.persistence import get_storage
from threatexchange.storage.interfaces import (
    ISignalTypeIndexStore,
    ISignalTypeConfigStore,
    IBankStore,
    SignalTypeIndexBuildCheckpoint,
)
from OpenMediaMatch.utils.time_utils import duration_to_human_str
from OpenMediaMatch.utils.memory_utils import trim_process_memory

logger = logging.getLogger(__name__)

# 4-hour safety timeout for the subprocess build.
_SUBPROCESS_TIMEOUT_SEC = 4 * 60 * 60


def _subprocess_build_target() -> None:
    """
    Entry point for the index-build child process.

    Creates its own Flask app (scheduler/cache disabled via OMM_SKIP_BACKGROUND_TASKS)
    and runs the full index build. When this process exits the OS reclaims
    all memory, which avoids RSS growth from C-level heap fragmentation
    caused by FAISS and other native allocators.
    """
    os.environ["OMM_SKIP_BACKGROUND_TASKS"] = "1"

    from OpenMediaMatch.app import create_app

    app = create_app()
    with app.app_context():
        storage = get_storage()
        build_all_indices(storage, storage, storage)


def apscheduler_build_all_indices() -> None:
    """
    APScheduler entry point — spawn an isolated subprocess for the build.

    FAISS indexes allocate large C++ buffers that fragment glibc's heap.
    Even after the Python references are dropped, free() cannot return
    interior pages to the OS, so RSS ratchets up with every build cycle.
    Running in a subprocess sidesteps this: the OS reclaims everything
    when the child exits.
    """
    app = get_apscheduler().app

    ctx = multiprocessing.get_context("spawn")
    proc = ctx.Process(target=_subprocess_build_target, name="omm-index-builder")
    proc.start()
    app.logger.info("Index build subprocess started (pid=%s)", proc.pid)

    proc.join(timeout=_SUBPROCESS_TIMEOUT_SEC)

    if proc.exitcode is None:
        app.logger.error(
            "Index build subprocess timed out after %ds (pid=%s), killing",
            _SUBPROCESS_TIMEOUT_SEC,
            proc.pid,
        )
        proc.kill()
        proc.join()
    elif proc.exitcode != 0:
        app.logger.error(
            "Index build subprocess exited with code %d (pid=%s)",
            proc.exitcode,
            proc.pid,
        )
    else:
        app.logger.info("Index build subprocess completed successfully")


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
        "Completed %s background task, took %s",
        build_all_indices.__name__,
        duration_to_human_str(time.time() - start),
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

    # Use try/finally to ensure aggressive memory trim after build
    signal_count = 0
    built_index: t.Any | None = None  # keep in locals per review nit

    try:
        built_index, checkpoint, signal_count = _prepare_index(
            for_signal_type, bank_store
        )
        index_store.store_signal_type_index(for_signal_type, built_index, checkpoint)
    finally:
        # Force garbage collection to reclaim memory and attempt to free pages
        # explicitly free the built index before reclaiming memory
        built_index = None
        trim_process_memory(logger, "Indexer")

    logger.info(
        "Indexed %d signals for %s - %s",
        signal_count,
        for_signal_type.get_name(),
        duration_to_human_str(time.time() - start),
    )


def _prepare_index(
    for_signal_type: t.Type[SignalType],
    bank_store: IBankStore,
) -> tuple[t.Any, SignalTypeIndexBuildCheckpoint, int]:
    """
    Collect signals for the given type, build the index, and compute checkpoint.
    Returns a tuple of (built_index, checkpoint, signal_count).
    """
    signal_list: list[tuple[str, int]] = []
    signal_count = 0
    last_cs = None

    # Collect signals
    for last_cs in bank_store.bank_yield_content(for_signal_type):
        signal_list.append((last_cs.signal_val, last_cs.bank_content_id))
        signal_count += 1

    # Build index
    index_cls = for_signal_type.get_index_cls()
    built_index = index_cls.build(signal_list)

    # explicitly free the signal list before returning
    signal_list.clear()

    # Create checkpoint
    checkpoint = SignalTypeIndexBuildCheckpoint.get_empty()
    if last_cs is not None:
        checkpoint = SignalTypeIndexBuildCheckpoint(
            last_item_timestamp=last_cs.bank_content_timestamp,
            last_item_id=last_cs.bank_content_id,
            total_hash_count=signal_count,
        )

    return built_index, checkpoint, signal_count
