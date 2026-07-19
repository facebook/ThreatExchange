"""Tests for the core ThreatExchange client."""

import os
import unittest
from unittest import mock

from fb_threatexchange import ThreatExchangeClient
from fb_threatexchange.models import ThreatType


class TestThreatExchangeClient(unittest.TestCase):
    """Test cases for ThreatExchangeClient."""

    def setUp(self) -> None:
        # Ensure ACCESS_TOKEN is present for every test; use patch.dict
        self._env_patcher = mock.patch.dict(os.environ, {"ACCESS_TOKEN": "test_token"})
        self._env_patcher.start()
        self.client = ThreatExchangeClient()

    def tearDown(self) -> None:
        self._env_patcher.stop()

    def test_client_initialization(self) -> None:
        """Test that the client initializes with correct attributes."""
        self.assertEqual(self.client.access_token, "test_token")
        self.assertEqual(self.client.base_url, ThreatExchangeClient.DEFAULT_BASE_URL)

    def test_client_custom_base_url(self) -> None:
        """Test that custom base URL is used when provided."""
        custom_url = "https://custom.api.com/v1"
        client = ThreatExchangeClient(base_url=custom_url)

        self.assertEqual(client.base_url, custom_url)

    def test_get_access_token(self) -> None:
        """Test access token generation."""
        # override for this specific assertion
        os.environ["ACCESS_TOKEN"] = "my_app_id|my_app_secret"
        
        client = ThreatExchangeClient()
        token = client.get_access_token()
        self.assertEqual(token, "my_app_id|my_app_secret")

    def test_get_threat_descriptors_returns_list(self) -> None:
        """Test that get_threat_descriptors returns a list."""
        result = self.client.get_threat_descriptors("test query")
        self.assertIsInstance(result, list)

    def test_get_threat_indicators_returns_list(self) -> None:
        """Test that get_threat_indicators returns a list."""
        result = self.client.get_threat_indicators("descriptor_123")
        self.assertIsInstance(result, list)

    def test_submit_descriptor_returns_success(self) -> None:
        """Test that submit_descriptor returns success response."""
        from fb_threatexchange import ThreatDescriptor, ThreatIndicator

        indicator = ThreatIndicator(
            id="ind_123",
            indicator="example.com",
            type=ThreatType.MALICIOUS_URL,
        )
        descriptor = ThreatDescriptor(
            id="desc_123",
            indicator=indicator,
            owner_id="owner_123",
        )

        result = self.client.submit_descriptor(descriptor)
        self.assertEqual(result.get("success"), True)

    @mock.patch("fb_threatexchange.core.requests.get")
    def test_get_members_parses_response(self, mock_get) -> None:
        """Test that get_members calls requests.get and parses JSON response."""
        fake_resp = mock.Mock()
        fake_resp.raise_for_status.return_value = None
        fake_resp.json.return_value = {"data": [{"id": "m1"}, {"id": "m2"}]}
        mock_get.return_value = fake_resp

        members = self.client.get_members()

        self.assertIsInstance(members, list)
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0]["id"], "m1")

        # Verify requests.get was called with expected params
        self.assertTrue(mock_get.called)
        _, kwargs = mock_get.call_args
        self.assertIn("params", kwargs)
        self.assertEqual(kwargs["params"], {"access_token": self.client.get_access_token()})


if __name__ == "__main__":
    unittest.main()

