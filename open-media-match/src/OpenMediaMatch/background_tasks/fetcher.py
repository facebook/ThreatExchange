# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import logging

from flask import current_app

from threatexchange.exchanges.fetch_state import CollaborationConfigBase

from OpenMediaMatch.background_tasks.development import get_apscheduler
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.storage.interface import ISignalExchangeStore, SignalType

logger = logging.getLogger(__name__)


def apscheduler_fetch_all() -> None:
    with get_apscheduler().app.app_context():
        storage = get_storage()
        fetch_all(storage, storage.get_enabled_signal_types())


def fetch_all(
    collab_store: ISignalExchangeStore,
    enabled_signal_types: t.Mapping[str, t.Type[SignalType]],
) -> None:
    """
    For all collaborations registered with OMM, fetch()
    """
    logger.info("Running the %s background task", fetch_all.__name__)
    collabs = collab_store.exchanges_get()
    for c in collabs.values():
        fetch(collab_store, enabled_signal_types, c)
    logger.info("Completed %s background task", fetch_all.__name__)


def fetch(
    config: ISignalExchangeStore,
    enabled_signal_types: t.Mapping[str, t.Type[SignalType]],
    collab: CollaborationConfigBase,
):
    """
    Fetch data from

    1. Attempt to authenticate with that collaboration's API
       using stored credentials.
    2. Load the fetch checkpoint from storage
    3. Resume the fetch at the checkpoint
    4. Download new data
    5. Send the new data to storage (saving the new checkpoint)
    """
    # TODO
