# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
from unittest.mock import MagicMock, patch

import pytest
from flask.testing import FlaskClient

from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.index import SignalTypeIndex, IndexMatchUntyped, SignalSimilarityInfo
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

    client = app.test_client()
    assert client.get("/status").status_code == 200
    return client


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
            assert "does not support query_top_k" in resp.json.get("error", "")

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
    """Test lookup_topk with a mocked external signal type that supports query_top_k."""
    client = client_with_sample_data

    storage = get_storage()
    
    # Use a mock external signal type not in ThreatExchange config
    mock_signal_type_name = "mock_external_signal"
    mock_signal_value = "abcd1234ef5678901234567890abcdef"  # 32 char mock signal
    
    # Mock signal type config
    mock_signal_config = MagicMock()
    mock_signal_config.enabled = True
    mock_signal_type = MagicMock()
    mock_signal_type.validate_signal_str.return_value = mock_signal_value
    mock_signal_config.signal_type = mock_signal_type

    # Mock the index to have query_top_k method
    mock_index = MagicMock(spec=SignalTypeIndex)
    mock_results = [
        IndexMatchUntyped(
            metadata=1001,
            similarity_info=MagicMock(pretty_str=lambda: "5")
        ),
        IndexMatchUntyped(
            metadata=1002,
            similarity_info=MagicMock(pretty_str=lambda: "3")
        ),
    ]
    mock_index.query_top_k.return_value = mock_results

    # Mock signals (32 char hex strings)
    mock_signal_1 = "1111222233334444555566667777aaaa"
    mock_signal_2 = "8888999900001111222233334444bbbb"
    mock_signals = {
        1001: {mock_signal_type_name: mock_signal_1},
        1002: {mock_signal_type_name: mock_signal_2},
    }

    with patch.object(storage, 'get_signal_type_configs', return_value={mock_signal_type_name: mock_signal_config}):
        with patch('OpenMediaMatch.blueprints.matching._get_index', return_value=mock_index):
            with patch.object(storage, 'bank_content_get_signals', return_value=mock_signals):
                query_str = {"signal": mock_signal_value, "signal_type": mock_signal_type_name, "k": "2"}
                resp = client.get("/m/lookup_topk", query_string=query_str)
                
                assert resp.status_code == 200
                matches = resp.json["matches"]  # type: ignore
                assert len(matches) == 2
                
                # Verify the first match has the correct signal
                assert matches[0]["bank_content_id"] == 1001
                assert matches[0]["signal"] == mock_signal_1
                assert len(matches[0]["signal"]) == 32
                
                # Verify the second match
                assert matches[1]["bank_content_id"] == 1002
                assert matches[1]["signal"] == mock_signal_2
                assert len(matches[1]["signal"]) == 32
                
                for match in matches:
                    assert "bank_content_id" in match
                    assert "distance" in match
                    assert "signal" in match
                    assert isinstance(match["bank_content_id"], int)


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
            assert "does not support query_threshold" in resp.json.get("error", "")

    # Test missing threshold parameter with first signal type
    sig_name = list(storage.get_signal_type_configs().keys())[0]
    signal_cfg = storage.get_signal_type_configs()[sig_name]
    sig_str = signal_cfg.signal_type.get_examples()[0]
    
    query_str = {"signal": sig_str, "signal_type": sig_name}
    resp = client.get("/m/lookup_threshold", query_string=query_str)
    assert resp.status_code == 400


def test_lookup_threshold_with_mock(client_with_sample_data: FlaskClient):
    """Test lookup_threshold with a mocked external signal type that supports query_threshold."""
    client = client_with_sample_data

    storage = get_storage()
    
    # Use a mock external signal type not in ThreatExchange config
    mock_signal_type_name = "mock_external_signal"
    mock_signal_value = "abcd1234ef5678901234567890abcdef"  # 32 char mock signal
    
    # Mock signal type config
    mock_signal_config = MagicMock()
    mock_signal_config.enabled = True
    mock_signal_type = MagicMock()
    mock_signal_type.validate_signal_str.return_value = mock_signal_value
    mock_signal_config.signal_type = mock_signal_type

    # Mock the index to have query_threshold method
    mock_index = MagicMock(spec=SignalTypeIndex)
    
    # Mock signals (32 char hex strings)
    mock_signal_1 = "1111222233334444555566667777aaaa"
    mock_signal_2 = "8888999900001111222233334444bbbb"
    mock_signal_3 = "ccccddddeeeefffff0000111122223333"
    
    # Mock results for threshold 80
    mock_results_80 = [
        IndexMatchUntyped(
            metadata=1001,
            similarity_info=MagicMock(pretty_str=lambda: "0")
        ),
        IndexMatchUntyped(
            metadata=1002,
            similarity_info=MagicMock(pretty_str=lambda: "68")
        ),
        IndexMatchUntyped(
            metadata=1003,
            similarity_info=MagicMock(pretty_str=lambda: "75")
        ),
    ]
    
    # Mock results for threshold 50 (tighter, fewer results)
    mock_results_50 = [
        IndexMatchUntyped(
            metadata=1001,
            similarity_info=MagicMock(pretty_str=lambda: "0")
        ),
    ]
    
    mock_index.query_threshold.side_effect = lambda sig, thresh: (
        mock_results_50 if thresh == "50" else mock_results_80
    )
    
    mock_signals = {
        1001: {mock_signal_type_name: mock_signal_1},
        1002: {mock_signal_type_name: mock_signal_2},
        1003: {mock_signal_type_name: mock_signal_3},
    }

    with patch.object(storage, 'get_signal_type_configs', return_value={mock_signal_type_name: mock_signal_config}):
        with patch('OpenMediaMatch.blueprints.matching._get_index', return_value=mock_index):
            with patch.object(storage, 'bank_content_get_signals', return_value=mock_signals):
                # Test with threshold 80
                query_str = {"signal": mock_signal_value, "signal_type": mock_signal_type_name, "threshold": "80"}
                resp = client.get("/m/lookup_threshold", query_string=query_str)
                assert resp.status_code == 200
                matches_80 = resp.json["matches"]  # type: ignore
                assert len(matches_80) == 3
                
                # Verify match structure and signals
                assert matches_80[0]["bank_content_id"] == 1001
                assert matches_80[0]["distance"] == "0"
                assert matches_80[0]["signal"] == mock_signal_1
                assert len(matches_80[0]["signal"]) == 32
                
                assert matches_80[1]["bank_content_id"] == 1002
                assert matches_80[1]["distance"] == "68"
                assert matches_80[1]["signal"] == mock_signal_2
                
                for match in matches_80:
                    assert "bank_content_id" in match
                    assert "distance" in match
                    assert "signal" in match
                    assert isinstance(match["bank_content_id"], int)

                # Test with tighter threshold 50
                query_str = {"signal": mock_signal_value, "signal_type": mock_signal_type_name, "threshold": "50"}
                resp = client.get("/m/lookup_threshold", query_string=query_str)
                assert resp.status_code == 200
                matches_50 = resp.json["matches"]  # type: ignore
                assert len(matches_50) == 1
                
                # Tighter threshold returns fewer matches
                assert len(matches_50) < len(matches_80)
