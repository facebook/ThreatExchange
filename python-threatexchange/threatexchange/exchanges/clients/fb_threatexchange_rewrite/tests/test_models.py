"""Tests for the ThreatExchange data models."""

import unittest
from datetime import datetime

from fb_threatexchange.models import (
    ShareLevel,
    Status,
    ThreatDescriptor,
    ThreatIndicator,
    ThreatType,
)


class TestThreatIndicator(unittest.TestCase):
    """Test cases for ThreatIndicator."""

    def test_indicator_creation(self) -> None:
        """Test basic indicator creation."""
        indicator = ThreatIndicator(
            id="ind_123",
            indicator="malware.example.com",
            type=ThreatType.MALICIOUS_URL,
        )

        self.assertEqual(indicator.id, "ind_123")
        self.assertEqual(indicator.indicator, "malware.example.com")
        self.assertEqual(indicator.type, ThreatType.MALICIOUS_URL)

    def test_indicator_with_timestamps(self) -> None:
        """Test indicator with timestamps."""
        now = datetime.now()
        indicator = ThreatIndicator(
            id="ind_123",
            indicator="test_hash",
            type=ThreatType.HASH_MD5,
            creation_time=now,
            last_updated=now,
        )

        self.assertEqual(indicator.creation_time, now)
        self.assertEqual(indicator.last_updated, now)

    def test_indicator_to_dict(self) -> None:
        """Test converting indicator to dictionary."""
        indicator = ThreatIndicator(
            id="ind_123",
            indicator="test.com",
            type=ThreatType.PHISHING,
        )

        result = indicator.to_dict()

        self.assertEqual(result["id"], "ind_123")
        self.assertEqual(result["indicator"], "test.com")
        self.assertEqual(result["type"], "PHISHING")


class TestThreatDescriptor(unittest.TestCase):
    """Test cases for ThreatDescriptor."""

    def setUp(self) -> None:
        """Create a sample indicator for testing."""
        self.sample_indicator = ThreatIndicator(
            id="ind_123",
            indicator="malware.example.com",
            type=ThreatType.MALICIOUS_URL,
        )

    def test_descriptor_creation(self) -> None:
        """Test basic descriptor creation."""
        descriptor = ThreatDescriptor(
            id="desc_123",
            indicator=self.sample_indicator,
            owner_id="owner_456",
        )

        self.assertEqual(descriptor.id, "desc_123")
        self.assertEqual(descriptor.indicator, self.sample_indicator)
        self.assertEqual(descriptor.owner_id, "owner_456")
        self.assertEqual(descriptor.status, Status.UNKNOWN)
        self.assertEqual(descriptor.share_level, ShareLevel.AMBER)

    def test_descriptor_with_all_fields(self) -> None:
        """Test descriptor with all fields populated."""
        now = datetime.now()
        descriptor = ThreatDescriptor(
            id="desc_123",
            indicator=self.sample_indicator,
            owner_id="owner_456",
            status=Status.MALICIOUS,
            share_level=ShareLevel.RED,
            description="A malicious URL",
            tags=["malware", "phishing"],
            creation_time=now,
            expire_time=now,
        )

        self.assertEqual(descriptor.status, Status.MALICIOUS)
        self.assertEqual(descriptor.share_level, ShareLevel.RED)
        self.assertEqual(descriptor.description, "A malicious URL")
        self.assertEqual(descriptor.tags, ["malware", "phishing"])

    def test_descriptor_to_dict(self) -> None:
        """Test converting descriptor to dictionary."""
        descriptor = ThreatDescriptor(
            id="desc_123",
            indicator=self.sample_indicator,
            owner_id="owner_456",
            status=Status.MALICIOUS,
            tags=["test"],
        )

        result = descriptor.to_dict()

        self.assertEqual(result["id"], "desc_123")
        self.assertEqual(result["owner_id"], "owner_456")
        self.assertEqual(result["status"], "MALICIOUS")
        self.assertEqual(result["tags"], ["test"])
        self.assertIn("indicator", result)

    def test_descriptor_from_dict(self) -> None:
        """Test creating descriptor from dictionary."""
        data = {
            "id": "desc_789",
            "indicator": {
                "id": "ind_789",
                "indicator": "spam.example.com",
                "type": "SPAM",
            },
            "owner_id": "owner_999",
            "status": "SUSPICIOUS",
            "share_level": "GREEN",
            "description": "Suspected spam domain",
            "tags": ["spam", "suspicious"],
        }

        descriptor = ThreatDescriptor.from_dict(data)

        self.assertEqual(descriptor.id, "desc_789")
        self.assertEqual(descriptor.owner_id, "owner_999")
        self.assertEqual(descriptor.status, Status.SUSPICIOUS)
        self.assertEqual(descriptor.share_level, ShareLevel.GREEN)
        self.assertEqual(descriptor.description, "Suspected spam domain")


class TestEnums(unittest.TestCase):
    """Test cases for enum values."""

    def test_threat_types(self) -> None:
        """Test ThreatType enum values."""
        self.assertEqual(ThreatType.MALWARE.value, "MALWARE")
        self.assertEqual(ThreatType.PHISHING.value, "PHISHING")
        self.assertEqual(ThreatType.HASH_PDQ.value, "HASH_PDQ")

    def test_share_levels(self) -> None:
        """Test ShareLevel enum values."""
        self.assertEqual(ShareLevel.WHITE.value, "WHITE")
        self.assertEqual(ShareLevel.GREEN.value, "GREEN")
        self.assertEqual(ShareLevel.AMBER.value, "AMBER")
        self.assertEqual(ShareLevel.RED.value, "RED")

    def test_status_values(self) -> None:
        """Test Status enum values."""
        self.assertEqual(Status.MALICIOUS.value, "MALICIOUS")
        self.assertEqual(Status.SUSPICIOUS.value, "SUSPICIOUS")
        self.assertEqual(Status.NON_MALICIOUS.value, "NON_MALICIOUS")
        self.assertEqual(Status.UNKNOWN.value, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()

