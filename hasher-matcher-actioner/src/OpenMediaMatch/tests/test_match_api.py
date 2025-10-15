# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

import pytest
from flask.testing import FlaskClient

from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
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
