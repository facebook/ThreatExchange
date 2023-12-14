# Copyright (c) Meta Platforms, Inc. and affiliates.

from dataclasses import dataclass
import typing as t
import logging
import datetime
import time

from threatexchange.exchanges.fetch_state import (
    CollaborationConfigBase,
    FetchDeltaTyped,
    NoCheckpointing,
)

from OpenMediaMatch.background_tasks.development import get_apscheduler
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.storage.interface import ISignalExchangeStore, SignalTypeConfig
from OpenMediaMatch.utils.time_utils import duration_to_human_str

logger = logging.getLogger(__name__)

COMMIT_TO_DB_MAX_SIZE = 5000
COMMIT_TO_DB_MAX_SEC = 60

ONE_FETCH_MAX_SEC = 60 * 4


def apscheduler_fetch_all() -> None:
    with get_apscheduler().app.app_context():
        storage = get_storage()
        fetch_all(storage, storage.get_signal_type_configs())


def fetch_all(
    collab_store: ISignalExchangeStore,
    signal_type_cfgs: t.Mapping[str, SignalTypeConfig],
) -> None:
    """
    For all collaborations registered with OMM, fetch()
    """
    logger.info("Running the %s background task", fetch_all.__name__)
    start = time.time()
    collabs = collab_store.exchanges_get()
    for c in collabs.values():
        fetch(collab_store, signal_type_cfgs, c)
    logger.info(
        "Completed %s background task - %s",
        fetch_all.__name__,
        duration_to_human_str(int(time.time() - start)),
    )


def fetch(
    collab_store: ISignalExchangeStore,
    signal_type_cfgs: t.Mapping[str, SignalTypeConfig],
    collab: CollaborationConfigBase,
):
    """Wrapper for exception recording"""
    start = time.time()
    try:
        collab_store.exchange_start_fetch(collab.name)
        _fetch(collab_store, signal_type_cfgs, collab)
    except Exception:
        logger.exception("%s[%s] Failed to fetch!", collab.name, collab.api)
        collab_store.exchange_complete_fetch(
            collab.name, is_up_to_date=False, exception=True
        )
    finally:
        logger.info(
            "%s[%s] Completed - %s",
            collab.name,
            collab.api,
            duration_to_human_str(int(time.time() - start)),
        )


def _fetch(
    collab_store: ISignalExchangeStore,
    signal_type_cfgs: t.Mapping[str, SignalTypeConfig],
    collab: CollaborationConfigBase,
):
    """
    Fetch data for a single collab.

    1. Attempt to authenticate with that collaboration's API
       using stored credentials.
    2. Load the fetch checkpoint from storage
    3. Resume the fetch at the checkpoint
    4. Download new data
    5. Send the new data to storage (saving the new checkpoint)
    """
    log = lambda msg, *args, level=logger.info: level(
        "%s[%s] " + msg, collab.name, collab.api, *args
    )
    log("Fetching signals for %s from %s", collab.name, collab.api)

    api_cls = collab_store.exchange_get_type_configs().get(collab.api)
    assert (
        api_cls is not None
    ), f"No such SignalExchangeAPI '{collab.api}' - maybe it was deleted?"

    api_client = api_cls.for_collab(collab)

    starting_checkpoint = collab_store.exchange_get_fetch_checkpoint(collab.name)
    checkpoint = starting_checkpoint

    if starting_checkpoint is None:
        log("No checkpoint, should be the first fetch.")
    else:
        if starting_checkpoint.is_stale():
            # This is a little jankey, but the stale behavior is actually fairly complex,
            # and we want to avoid triggering on trivial fetching
            if isinstance(starting_checkpoint, NoCheckpointing):
                log(
                    "Is a NoCheckpointing class, which hopefully is a test type, "
                    "and we have a checkpoint. Considering complete"
                )
                collab_store.exchange_complete_fetch(
                    collab.name, is_up_to_date=True, exception=False
                )
                return
            log("Checkpoint has become stale! Will refetch from scratch")
            checkpoint = None
        else:
            ts = starting_checkpoint.get_progress_timestamp()
            if ts is not None:
                log("Resuming from %s", _timeformat(ts))
            else:
                log("Resuming from stored checkpoint (no progress time)")

    signal_types = [stc.signal_type for stc in signal_type_cfgs.values()]

    fetch_start = time.time()
    last_db_commit = fetch_start
    up_to_date = False
    pending_merge: t.Optional[FetchDeltaTyped] = None

    delta: FetchDeltaTyped
    for delta in api_client.fetch_iter(signal_types, checkpoint):
        assert delta.checkpoint is not None  # Infinite loop protection
        progress_time = delta.checkpoint.get_progress_timestamp()
        log(
            "fetch_iter() with %d new records%s",
            len(delta.updates),
            ("" if progress_time is None else f" @ {_timeformat(progress_time)}"),
            level=logger.debug,
        )
        pending_merge = _merge_delta(pending_merge, delta)
        next_checkpoint = delta.checkpoint

        if checkpoint is not None:
            prev_time = checkpoint.get_progress_timestamp()
            if prev_time is not None and progress_time is not None:
                assert prev_time <= progress_time, (
                    "checkpoint time rewound? ",
                    "This can indicate a serious ",
                    "problem with the API and checkpointing",
                )
        checkpoint = next_checkpoint  # Only used for the rewind check

        if _should_commit(pending_merge, last_db_commit):
            log("Committing progress...")
            collab_store.exchange_commit_fetch(
                collab,
                starting_checkpoint,
                pending_merge.updates,
                pending_merge.checkpoint,
            )
            starting_checkpoint = pending_merge.checkpoint
            pending_merge = None
            last_db_commit = time.time()
        if _hit_single_config_limit(fetch_start):
            log("Hit limit for one config fetch")
            break
    else:
        up_to_date = True
        log("Fetched all data! Up to date!")

    if pending_merge is not None:
        log("Committing progress...")
        collab_store.exchange_commit_fetch(
            collab,
            starting_checkpoint,
            pending_merge.updates,
            pending_merge.checkpoint,
        )

    collab_store.exchange_complete_fetch(
        collab.name, is_up_to_date=up_to_date, exception=False
    )


def _merge_delta(
    into: t.Optional[FetchDeltaTyped], new: FetchDeltaTyped
) -> FetchDeltaTyped:
    if into is None:
        return new
    into.updates.update(new.updates)
    into.checkpoint = new.checkpoint
    return into


def _hit_single_config_limit(start_time: float) -> bool:
    return time.time() - start_time > ONE_FETCH_MAX_SEC


def _should_commit(delta: FetchDeltaTyped, last_commit: float) -> bool:
    if len(delta.updates) >= COMMIT_TO_DB_MAX_SIZE:
        return True
    return time.time() - last_commit >= COMMIT_TO_DB_MAX_SEC


def _timeformat(timestamp: int) -> str:
    return datetime.datetime.fromtimestamp(timestamp).isoformat()
