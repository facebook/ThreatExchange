# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
from unittest.mock import MagicMock, patch

import pytest
from flask.testing import FlaskClient

from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.index import IndexMatchUntyped, SignalSimilarityInfo
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI

from OpenMediaMatch.tests.utils import app

from OpenMediaMatch.background_tasks import fetcher, build_index
from OpenMediaMatch.blueprints.matching import TMatchByBank
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.storage import interface as iface


@pytest.fixture()
def client_with_sample_data(app) -> FlaskClient:
    storage = get_storage()
    storage.exchange_api_config_update(
        iface.SignalExchangeAPIConfig(StaticSampleSignalExchangeAPI)
    )
    storage.exchange_update(
        StaticSampleSignalExchangeAPI.get_config_cls()(
            name="SAMPLE",
            api=StaticSampleSignalExchangeAPI.get_name(),
            enabled=True,
        ),
        create=True,
    )
    fetcher.fetch_all(storage, storage.get_signal_type_configs())
    build_index.build_all_indices(storage, storage, storage)

    return app.test_client()


# Helper functions for mock-based tests
def _create_mock_signal_config(signal_value: str) -> t.Tuple[MagicMock, str]:
    """Create a mock signal type config for testing."""
    mock_signal_config = MagicMock()
    mock_signal_config.enabled = True
    mock_signal_type = MagicMock()
    mock_signal_type.validate_signal_str.return_value = signal_value
    mock_signal_config.signal_type = mock_signal_type
    return mock_signal_config, signal_value


def _create_mock_index(
    topk_results: t.Optional[t.List[IndexMatchUntyped]] = None,
    threshold_behavior: t.Optional[
        t.Callable[[t.Any, str], t.List[IndexMatchUntyped]]
    ] = None,
) -> MagicMock:
    """
    Create a mock index with query_top_k and/or query_threshold methods.

    Args:
        topk_results: List of results sorted by distance for query_top_k (returns first k)
        threshold_behavior: Callable that takes (signal, threshold) and returns filtered results
    """
    mock_index = MagicMock()

    if topk_results is not None:
        mock_index.query_top_k.side_effect = lambda sig, k: topk_results[:k]

    if threshold_behavior is not None:
        mock_index.query_threshold.side_effect = threshold_behavior

    return mock_index


def _create_mock_signals(signal_type_name: str) -> t.Dict[int, t.Dict[str, str]]:
    """Create mock signal data for testing."""
    return {
        1001: {signal_type_name: "signal_1"},
        1002: {signal_type_name: "signal_2"},
        1003: {signal_type_name: "signal_3"},
    }


def test_raw_lookups(client_with_sample_data: FlaskClient):
    client = client_with_sample_data

    storage = get_storage()
    assert set(storage.get_signal_type_configs()) == {
        PdqSignal.get_name(),
        VideoMD5Signal.get_name(),
    }
    for sig_name, signal_cfg in storage.get_signal_type_configs().items():
        assert signal_cfg.enabled

        # For each type, just lookup one signal
        sig_str = signal_cfg.signal_type.get_examples()[0]

        query_str = {"signal": sig_str, "signal_type": sig_name}

        resp = client.get("/m/raw_lookup", query_string=query_str)
        assert resp.status_code == 200
        match_count = len(resp.json["matches"])  # type: ignore
        assert match_count >= 1

        # With distance
        query_str["include_distance"] = True  # type: ignore
        resp = client.get("/m/raw_lookup", query_string=query_str)
        assert resp.status_code == 200
        with_dist_matches = resp.json["matches"]  # type: ignore
        assert len(with_dist_matches) == match_count

        for match in with_dist_matches:
            assert "bank_content_id" in match
            assert "distance" in match


def test_lookups(client_with_sample_data: FlaskClient):
    client = client_with_sample_data

    storage = get_storage()
    # sanity check
    assert set(storage.get_signal_type_configs()) == {
        PdqSignal.get_name(),
        VideoMD5Signal.get_name(),
    }
    for sig_name, signal_cfg in storage.get_signal_type_configs().items():
        assert signal_cfg.enabled

        # For each type, just lookup one signal
        sig_str = signal_cfg.signal_type.get_examples()[0]

        query_str = {"signal": sig_str, "signal_type": sig_name}

        resp = client.get("/m/lookup", query_string=query_str)
        assert resp.status_code == 200
        resp_json = t.cast(TMatchByBank, resp.json)
        assert len(resp_json) == 1
        assert "SAMPLE" in resp_json
        with_dist_matches = resp_json["SAMPLE"]
        assert len(with_dist_matches) > 0

        for match in with_dist_matches:
            assert "bank_content_id" in match
            assert "distance" in match


def test_lookup_topk(client_with_sample_data: FlaskClient):
    """Test the lookup_topk endpoint."""
    client = client_with_sample_data

    storage = get_storage()
    # Test with all configured signal types - they should return 501 if unsupported
    for sig_name, signal_cfg in storage.get_signal_type_configs().items():
        sig_str = signal_cfg.signal_type.get_examples()[0]

        query_str = {"signal": sig_str, "signal_type": sig_name, "k": "3"}
        resp = client.get("/m/lookup_topk", query_string=query_str)
        # Should return 501 if the signal type doesn't support query_top_k
        assert resp.status_code in [200, 501]
        if resp.status_code == 501:
            assert resp.json is not None
            assert "does not support query_top_k" in resp.json.get("message", "")

    # Test missing k parameter with first signal type
    sig_name = list(storage.get_signal_type_configs().keys())[0]
    signal_cfg = storage.get_signal_type_configs()[sig_name]
    sig_str = signal_cfg.signal_type.get_examples()[0]

    query_str = {"signal": sig_str, "signal_type": sig_name}
    resp = client.get("/m/lookup_topk", query_string=query_str)
    assert resp.status_code == 400

    # Test invalid k parameter
    query_str = {"signal": sig_str, "signal_type": sig_name, "k": "invalid"}
    resp = client.get("/m/lookup_topk", query_string=query_str)
    assert resp.status_code == 400


def test_lookup_topk_with_mock(client_with_sample_data: FlaskClient):
    """Test lookup_topk returns K closest matches in sorted order."""
    client = client_with_sample_data
    storage = get_storage()

    mock_signal_type_name = "mock_external_signal"
    mock_signal_value = "abcd1234ef5678901234567890abcdef"

    topk_results = [
        IndexMatchUntyped(
            metadata=1002, similarity_info=MagicMock(pretty_str=lambda: "3")
        ),
        IndexMatchUntyped(
            metadata=1001, similarity_info=MagicMock(pretty_str=lambda: "5")
        ),
        IndexMatchUntyped(
            metadata=1003, similarity_info=MagicMock(pretty_str=lambda: "8")
        ),
    ]

    mock_signal_config, _ = _create_mock_signal_config(mock_signal_value)
    mock_index = _create_mock_index(topk_results=topk_results)
    mock_signals = _create_mock_signals(mock_signal_type_name)

    with patch.object(
        storage,
        "get_signal_type_configs",
        return_value={mock_signal_type_name: mock_signal_config},
    ), patch(
        "OpenMediaMatch.blueprints.matching._get_index", return_value=mock_index
    ), patch.object(
        storage, "bank_content_get_signals", return_value=mock_signals
    ):
        resp = client.get(
            "/m/lookup_topk",
            query_string={
                "signal": mock_signal_value,
                "signal_type": mock_signal_type_name,
                "k": "2",
            },
        )

        assert resp.status_code == 200
        matches = resp.json["matches"]  # type: ignore
        assert len(matches) == 2
        assert matches[0]["bank_content_id"] == 1002
        assert matches[1]["bank_content_id"] == 1001


def test_lookup_threshold(client_with_sample_data: FlaskClient):
    """Test the lookup_threshold endpoint."""
    client = client_with_sample_data

    storage = get_storage()
    # Test with all configured signal types - they should return 501 if unsupported
    for sig_name, signal_cfg in storage.get_signal_type_configs().items():
        sig_str = signal_cfg.signal_type.get_examples()[0]

        query_str = {"signal": sig_str, "signal_type": sig_name, "threshold": "10"}
        resp = client.get("/m/lookup_threshold", query_string=query_str)
        # Should return 501 if the signal type doesn't support query_threshold
        assert resp.status_code in [200, 501]
        if resp.status_code == 501:
            assert resp.json is not None
            assert "does not support query_threshold" in resp.json.get("message", "")

    # Test missing threshold parameter with first signal type
    sig_name = list(storage.get_signal_type_configs().keys())[0]
    signal_cfg = storage.get_signal_type_configs()[sig_name]
    sig_str = signal_cfg.signal_type.get_examples()[0]

    query_str = {"signal": sig_str, "signal_type": sig_name}
    resp = client.get("/m/lookup_threshold", query_string=query_str)
    assert resp.status_code == 400


def test_lookup_threshold_with_mock(client_with_sample_data: FlaskClient):
    """Test lookup_threshold filters results based on threshold parameter."""
    client = client_with_sample_data
    storage = get_storage()

    mock_signal_type_name = "mock_external_signal"
    mock_signal_value = "abcd1234ef5678901234567890abcdef"

    def threshold_behavior(sig: t.Any, thresh: str) -> t.List[IndexMatchUntyped]:
        if thresh == "50":
            return [
                IndexMatchUntyped(
                    metadata=1001, similarity_info=MagicMock(pretty_str=lambda: "0")
                ),
            ]
        else:  # threshold 80
            return [
                IndexMatchUntyped(
                    metadata=1001, similarity_info=MagicMock(pretty_str=lambda: "0")
                ),
                IndexMatchUntyped(
                    metadata=1002, similarity_info=MagicMock(pretty_str=lambda: "68")
                ),
                IndexMatchUntyped(
                    metadata=1003, similarity_info=MagicMock(pretty_str=lambda: "75")
                ),
            ]

    mock_signal_config, _ = _create_mock_signal_config(mock_signal_value)
    mock_index = _create_mock_index(threshold_behavior=threshold_behavior)
    mock_signals = _create_mock_signals(mock_signal_type_name)

    with patch.object(
        storage,
        "get_signal_type_configs",
        return_value={mock_signal_type_name: mock_signal_config},
    ), patch(
        "OpenMediaMatch.blueprints.matching._get_index", return_value=mock_index
    ), patch.object(
        storage, "bank_content_get_signals", return_value=mock_signals
    ):
        resp = client.get(
            "/m/lookup_threshold",
            query_string={
                "signal": mock_signal_value,
                "signal_type": mock_signal_type_name,
                "threshold": "80",
            },
        )
        assert resp.status_code == 200
        assert len(resp.json["matches"]) == 3  # type: ignore

        resp = client.get(
            "/m/lookup_threshold",
            query_string={
                "signal": mock_signal_value,
                "signal_type": mock_signal_type_name,
                "threshold": "50",
            },
        )
        assert resp.status_code == 200
        assert len(resp.json["matches"]) == 1  # type: ignore


@pytest.fixture()
def client_with_multi_bank_data(app) -> FlaskClient:
    """Fixture that sets up multiple banks with sample data for testing bank filtering."""
    storage = get_storage()

    # Create multiple banks
    storage.bank_update(iface.BankConfig("BANK_A", 1.0), create=True)
    storage.bank_update(iface.BankConfig("BANK_B", 1.0), create=True)
    storage.bank_update(iface.BankConfig("BANK_C", 1.0), create=True)

    # Add content to each bank using PDQ signals
    pdq_signal = PdqSignal.get_examples()[0]
    storage.bank_add_content("BANK_A", {PdqSignal: pdq_signal})
    storage.bank_add_content("BANK_B", {PdqSignal: pdq_signal})
    storage.bank_add_content("BANK_C", {PdqSignal: pdq_signal})

    # Build indices
    build_index.build_all_indices(storage, storage, storage)

    client = app.test_client()
    assert client.get("/status").status_code == 200
    return client


def test_raw_lookup_with_bank_filter(client_with_multi_bank_data: FlaskClient):
    """Test /m/raw_lookup endpoint with bank filtering."""
    client = client_with_multi_bank_data

    sig_str = PdqSignal.get_examples()[0]
    query_str = {"signal": sig_str, "signal_type": PdqSignal.get_name()}

    # Test without bank filter - should return all banks
    resp = client.get("/m/raw_lookup", query_string=query_str)
    assert resp.status_code == 200
    all_matches = resp.json["matches"]  # type: ignore
    assert len(all_matches) == 3  # One from each bank

    # Test filtering by single bank
    query_str["banks"] = "BANK_A"
    resp = client.get("/m/raw_lookup", query_string=query_str)
    assert resp.status_code == 200
    bank_a_matches = resp.json["matches"]  # type: ignore
    assert len(bank_a_matches) == 1

    # Test filtering by multiple banks
    query_str["banks"] = "BANK_A,BANK_B"
    resp = client.get("/m/raw_lookup", query_string=query_str)
    assert resp.status_code == 200
    multi_bank_matches = resp.json["matches"]  # type: ignore
    assert len(multi_bank_matches) == 2

    # Test filtering by non-existent bank
    query_str["banks"] = "NON_EXISTENT_BANK"
    resp = client.get("/m/raw_lookup", query_string=query_str)
    assert resp.status_code == 200
    no_matches = resp.json["matches"]  # type: ignore
    assert len(no_matches) == 0


def test_raw_lookup_with_distance_and_bank_filter(
    client_with_multi_bank_data: FlaskClient,
):
    """Test /m/raw_lookup with both distance and bank filtering."""
    client = client_with_multi_bank_data

    sig_str = PdqSignal.get_examples()[0]
    query_str = {
        "signal": sig_str,
        "signal_type": PdqSignal.get_name(),
        "include_distance": True,
        "banks": "BANK_A,BANK_B",
    }

    resp = client.get("/m/raw_lookup", query_string=query_str)
    assert resp.status_code == 200
    matches = resp.json["matches"]  # type: ignore
    assert len(matches) == 2

    for match in matches:
        assert "bank_content_id" in match
        assert "distance" in match


def test_lookup_with_bank_filter(client_with_multi_bank_data: FlaskClient):
    """Test /m/lookup endpoint with bank filtering."""
    client = client_with_multi_bank_data

    sig_str = PdqSignal.get_examples()[0]
    query_str = {"signal": sig_str, "signal_type": PdqSignal.get_name()}

    # Test without bank filter - should return all banks
    resp = client.get("/m/lookup", query_string=query_str)
    assert resp.status_code == 200
    resp_json = t.cast(TMatchByBank, resp.json)
    assert len(resp_json) == 3
    assert "BANK_A" in resp_json
    assert "BANK_B" in resp_json
    assert "BANK_C" in resp_json

    # Test filtering by single bank
    query_str["banks"] = "BANK_A"
    resp = client.get("/m/lookup", query_string=query_str)
    assert resp.status_code == 200
    resp_json = t.cast(TMatchByBank, resp.json)
    assert len(resp_json) == 1
    assert "BANK_A" in resp_json
    assert len(resp_json["BANK_A"]) > 0

    # Test filtering by multiple banks
    query_str["banks"] = "BANK_A,BANK_C"
    resp = client.get("/m/lookup", query_string=query_str)
    assert resp.status_code == 200
    resp_json = t.cast(TMatchByBank, resp.json)
    assert len(resp_json) == 2
    assert "BANK_A" in resp_json
    assert "BANK_C" in resp_json
    assert "BANK_B" not in resp_json

    # Test filtering by non-existent bank
    query_str["banks"] = "NON_EXISTENT_BANK"
    resp = client.get("/m/lookup", query_string=query_str)
    assert resp.status_code == 200
    resp_json = t.cast(TMatchByBank, resp.json)
    assert len(resp_json) == 0
