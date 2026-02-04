# Copyright (c) Meta Platforms, Inc. and affiliates.

"""Tests for the OpenAI Moderation classifier."""

import pytest
import typing as t

from threatexchange.classifier.openai_moderation import (
    MissingAPIKeyError,
    ModerationClassificationInfo,
    OpenAIModerationClassifier,
)
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.text import TextContent

SAMPLE_RESPONSE_SAFE: t.Dict[str, t.Any] = {
    "id": "modr-123",
    "model": "text-moderation-007",
    "results": [
        {
            "flagged": False,
            "categories": {"sexual": False, "hate": False, "harassment": False},
            "category_scores": {"sexual": 0.0001, "hate": 0.0002, "harassment": 0.0003},
        }
    ],
}

SAMPLE_RESPONSE_FLAGGED: t.Dict[str, t.Any] = {
    "id": "modr-456",
    "model": "text-moderation-007",
    "results": [
        {
            "flagged": True,
            "categories": {"sexual": False, "hate": True, "harassment": True},
            "category_scores": {"sexual": 0.01, "hate": 0.85, "harassment": 0.72},
        }
    ],
}


class MockResponse:
    def __init__(self, json_data: t.Dict[str, t.Any]):
        self._json_data = json_data

    def json(self) -> t.Dict[str, t.Any]:
        return self._json_data

    def raise_for_status(self) -> None:
        pass


def test_api_key_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test API key from env, explicit, and missing."""
    # Missing raises error
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError):
        OpenAIModerationClassifier()

    # From env
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
    assert OpenAIModerationClassifier().api_key == "sk-from-env"

    # Explicit takes precedence
    assert OpenAIModerationClassifier(api_key="sk-explicit").api_key == "sk-explicit"


def test_parse_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test parsing safe, flagged, and empty responses."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    classifier = OpenAIModerationClassifier()

    # Safe response
    result = classifier._parse_response(SAMPLE_RESPONSE_SAFE)
    assert not result.has_match
    assert all(not info.is_match for info in result.labels.values())

    # Flagged response
    result = classifier._parse_response(SAMPLE_RESPONSE_FLAGGED)
    assert result.has_match
    assert result.labels["hate"].is_match and result.labels["hate"].score == 0.85
    assert (
        result.labels["harassment"].is_match
        and result.labels["harassment"].score == 0.72
    )
    assert not result.labels["sexual"].is_match

    # Empty response
    result = classifier._parse_response({"results": []})
    assert not result.has_match and len(result.labels) == 0


def test_classify_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test full classification with mocked HTTP."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    import requests

    monkeypatch.setattr(
        requests, "post", lambda *a, **kw: MockResponse(SAMPLE_RESPONSE_FLAGGED)
    )

    classifier = OpenAIModerationClassifier()

    # Via classify() with TextContent
    result = classifier.classify(TextContent, "test")
    assert "hate" in result.positive_labels

    # Via classify_text()
    result = classifier.classify_text("test")
    assert "harassment" in result.positive_labels

    # Via classify() with PhotoContent
    result = classifier.classify(PhotoContent, "https://example.com/image.jpg")
    assert "hate" in result.positive_labels

    # Wrong content type
    from threatexchange.content_type.url import URLContent

    with pytest.raises(ValueError, match="Unsupported content type"):
        classifier.classify(URLContent, "test")


def test_classification_info() -> None:
    """Test ModerationClassificationInfo and string output."""
    info = ModerationClassificationInfo(is_match=True, score=0.95)
    assert info.weight_str() == "95.00%" and str(info) == "95.00%"

    info = ModerationClassificationInfo(is_match=False, score=0.01)
    assert info.weight_str() == "1.00%"


def test_class_metadata() -> None:
    """Test class-level attributes and methods."""
    assert OpenAIModerationClassifier.get_name() == "open_ai_moderation"
    content_types = OpenAIModerationClassifier.get_content_types()
    assert TextContent in content_types
    assert PhotoContent in content_types
    assert "sexual/minors" in OpenAIModerationClassifier.CATEGORY_LABELS
    assert OpenAIModerationClassifier.CATEGORY_LABELS["sexual/minors"] == "csam"


def test_classify_image(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Test image classification with URL and local file."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    captured_payloads: t.List[t.Dict[str, t.Any]] = []

    def mock_post(*args, **kwargs):
        captured_payloads.append(kwargs.get("json", {}))
        return MockResponse(SAMPLE_RESPONSE_FLAGGED)

    import requests

    monkeypatch.setattr(requests, "post", mock_post)

    classifier = OpenAIModerationClassifier()

    # Test URL passthrough
    result = classifier.classify_image("https://example.com/image.jpg")
    assert result.has_match
    payload = captured_payloads[-1]
    assert payload["input"][0]["type"] == "image_url"
    assert payload["input"][0]["image_url"]["url"] == "https://example.com/image.jpg"

    # Test local file (base64 encoded)
    test_image = tmp_path / "test.png"
    test_image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)  # Minimal PNG header

    result = classifier.classify_image(str(test_image))
    assert result.has_match
    payload = captured_payloads[-1]
    assert payload["input"][0]["type"] == "image_url"
    url = payload["input"][0]["image_url"]["url"]
    assert url.startswith("data:image/png;base64,")


def test_classify_multi(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test multi-modal classification with image and text."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    captured_payloads: t.List[t.Dict[str, t.Any]] = []

    def mock_post(*args, **kwargs):
        captured_payloads.append(kwargs.get("json", {}))
        return MockResponse(SAMPLE_RESPONSE_FLAGGED)

    import requests

    monkeypatch.setattr(requests, "post", mock_post)

    classifier = OpenAIModerationClassifier()

    result = classifier.classify_multi(
        "https://example.com/image.jpg", "alt text caption"
    )
    assert result.has_match

    payload = captured_payloads[-1]
    assert len(payload["input"]) == 2

    # First element should be text
    assert payload["input"][0]["type"] == "text"
    assert payload["input"][0]["text"] == "alt text caption"

    # Second element should be image
    assert payload["input"][1]["type"] == "image_url"
    assert payload["input"][1]["image_url"]["url"] == "https://example.com/image.jpg"
