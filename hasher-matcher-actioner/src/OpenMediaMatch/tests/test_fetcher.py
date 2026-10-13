# Copyright (c) Meta Platforms, Inc. and affiliates.

from unittest.mock import MagicMock, call, create_autospec, patch

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.storage.interfaces import ISignalExchangeStore

from OpenMediaMatch.background_tasks import fetcher


def _collab(name: str, enabled: bool = True) -> CollaborationConfigBase:
    return CollaborationConfigBase(
        name=name, api=StaticSampleSignalExchangeAPI.get_name(), enabled=enabled
    )


def _store(*collabs: CollaborationConfigBase) -> MagicMock:
    store = create_autospec(ISignalExchangeStore, instance=True)
    store.exchanges_get.return_value = {c.name: c for c in collabs}
    store.exchange_get_fetch_checkpoint.return_value = None
    store.exchange_get_client.return_value.fetch_iter.return_value = []
    return store


def test_disabled_exchange_is_not_marked_as_fetching():
    store = _store(_collab("DISABLED", enabled=False))

    fetcher.fetch_all(store, {})

    store.exchange_start_fetch.assert_not_called()
    store.exchange_complete_fetch.assert_not_called()


def test_fetch_failure_is_recorded_and_run_continues():
    store = _store(_collab("BROKEN"), _collab("HEALTHY"))

    def get_client(collab: CollaborationConfigBase) -> MagicMock:
        client = MagicMock()
        if collab.name == "BROKEN":
            client.fetch_iter.side_effect = RuntimeError("403 Forbidden")
        else:
            client.fetch_iter.return_value = []
        return client

    store.exchange_get_client.side_effect = get_client

    with patch.object(fetcher.random, "shuffle"):
        fetcher.fetch_all(store, {})

    store.exchange_complete_fetch.assert_has_calls(
        [
            call("BROKEN", is_up_to_date=False, exception=True),
            call("HEALTHY", is_up_to_date=True, exception=False),
        ]
    )


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

    # Keep BROKEN first so its error has a following exchange to skip
    with patch.object(fetcher.random, "shuffle"):
        fetcher.fetch_all(store, {})

    store.exchange_start_fetch.assert_any_call("HEALTHY")
    store.exchange_complete_fetch.assert_any_call(
        "HEALTHY", is_up_to_date=True, exception=False
    )


def test_every_enabled_exchange_fetched_once_in_shuffled_order():
    names = [f"EX_{i}" for i in range(5)]
    store = _store(*(_collab(n) for n in names), _collab("OFF", enabled=False))

    with patch.object(
        fetcher.random, "shuffle", side_effect=lambda items: items.reverse()
    ) as shuffle:
        fetcher.fetch_all(store, {})

    shuffle.assert_called_once()
    started = [c.args[0] for c in store.exchange_start_fetch.call_args_list]
    assert started == list(reversed(names))
