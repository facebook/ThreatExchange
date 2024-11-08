# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import pytest
import collections.abc

from threatexchange.exchanges.clients.fb_threatexchange.api import ThreatExchangeAPI
from threatexchange.exchanges.clients.fb_threatexchange.api_representations import (
    ThreatPrivacyGroup,
)

THREAT_EXCHANGE_INTEGRATION_TEST_TOKEN = os.getenv(
    "THREAT_EXCHANGE_INTEGRATION_TEST_TOKEN"
)


@pytest.fixture
def api():
    return ThreatExchangeAPI(THREAT_EXCHANGE_INTEGRATION_TEST_TOKEN)


need_token = pytest.mark.skipif(
    not THREAT_EXCHANGE_INTEGRATION_TEST_TOKEN,
    reason="Integration Test requires tokens. Use THREAT_EXCHANGE_INTEGRATION_TEST_TOKEN environment variable.",
)


@need_token
def test_get_threat_privacy_groups_member(api):
    """
    Assumes that the app (if token is provided) will have at least one
    privacy group.
    """
    response = api.get_threat_privacy_groups_member()
    assert isinstance(response, collections.abc.Sequence) and not isinstance(
        response, (str, bytes)
    ), "API returned something that's not a list!"
    assert isinstance(response[0], ThreatPrivacyGroup)
