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
