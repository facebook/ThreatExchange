# Copyright (c) Meta Platforms, Inc. and affiliates.

from unittest.mock import MagicMock

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI

from OpenMediaMatch.background_tasks import fetcher


def _collab(name: str, enabled: bool = True) -> CollaborationConfigBase:
    return CollaborationConfigBase(
        name=name, api=StaticSampleSignalExchangeAPI.get_name(), enabled=enabled
    )


def _store(*collabs: CollaborationConfigBase) -> MagicMock:
    store = MagicMock()
    store.exchanges_get.return_value = {c.name: c for c in collabs}
    store.exchange_get_fetch_checkpoint.return_value = None
    store.exchange_get_client.return_value.fetch_iter.return_value = []
    return store


def test_disabled_exchange_is_not_marked_as_fetching():
    store = _store(_collab("DISABLED", enabled=False))

    fetcher.fetch_all(store, {})

    store.exchange_start_fetch.assert_not_called()
    store.exchange_complete_fetch.assert_not_called()


def test_failure_recording_error_does_not_stop_other_exchanges():
    store = _store(_collab("BROKEN"), _collab("HEALTHY"))

    def start_fetch(name: str) -> None:
        if name == "BROKEN":
            raise RuntimeError("fetch failed")

    def complete_fetch(name: str, **kwargs) -> None:
        if name == "BROKEN":
            raise RuntimeError("could not record failure")

    store.exchange_start_fetch.side_effect = start_fetch
    store.exchange_complete_fetch.side_effect = complete_fetch

    fetcher.fetch_all(store, {})

    store.exchange_start_fetch.assert_any_call("HEALTHY")
    store.exchange_complete_fetch.assert_any_call(
        "HEALTHY", is_up_to_date=True, exception=False
    )
