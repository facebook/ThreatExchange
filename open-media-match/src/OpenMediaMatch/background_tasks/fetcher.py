# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

from OpenMediaMatch.storage.interface import ICollaborationStore, SignalType
from threatexchange.exchanges.fetch_state import CollaborationConfigBase


def fetch_all(
    collab_store: ICollaborationStore,
    enabled_signal_types: t.Dict[str, t.Type[SignalType]],
) -> None:
    """
    For all collaborations registered with OMM, fetch()
    """
    collabs = collab_store.get_collaborations()
    for c in collabs.values():
        fetch(collab_store, enabled_signal_types, c)


def fetch(
    config: ICollaborationStore,
    enabled_signal_types: t.Dict[str, t.Type[SignalType]],
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
