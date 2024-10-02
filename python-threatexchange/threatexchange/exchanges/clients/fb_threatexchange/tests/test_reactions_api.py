# Copyright (c) Meta Platforms, Inc. and affiliates.

from unittest.mock import Mock
import typing as t
import pytest
import requests

from threatexchange.exchanges.clients.fb_threatexchange.api import (
    ThreatExchangeAPI,
)

POST_SUCCESS = """
    {
        "succcess": true
    }
"""

POST_SUCCESS_JSON = {
        "succcess": True
}


def mock_post_impl(url: str, data: str, **params):
    content = POST_SUCCESS
    # Void your warantee by messing with requests state
    resp = requests.Response()
    resp._content = content.encode()
    resp.status_code = 200
    resp.content  # Set the rest of Request's internal state
    return resp

def test_matched_upvote_downvote(monkeypatch: pytest.MonkeyPatch):
    api = ThreatExchangeAPI("fake api token")
    session = Mock(
        strict_spec=["post", "__enter__", "__exit__"],
        post=mock_post_impl,
        __enter__=lambda _: session,
        __exit__=lambda *args: None,
    )
    monkeypatch.setattr(api, "_get_session", lambda: session)

    result = api.react_matched_threat_descriptor(1234, showURLs=False, dryRun=False)

    assert result[2] == POST_SUCCESS_JSON
    assert result[0] is None
    assert result[1] is None
    
    result = api.react_upvote_threat_descriptor(1234, showURLs=False, dryRun=False)

    assert result[2] == POST_SUCCESS_JSON
    assert result[0] is None
    assert result[1] is None

    result = api.react_downvote_threat_descriptor(1234, showURLs=False, dryRun=False)

    assert result[2] == POST_SUCCESS_JSON
    assert result[0] is None
    assert result[1] is None