# Copyright (c) Meta Platforms, Inc. and affiliates.

"""Tests for the OpenAI Moderation classifier."""

import os
import pytest
import typing as t

from threatexchange.classifier.openai_moderation import (
    MissingAPIKeyError,
    ModerationClassificationInfo,
    OpenAIModerationClassifier,
)
from threatexchange.content_type.text import TextContent


SAMPLE_RESPONSE_SAFE: t.Dict[str, t.Any] = {
    "id": "modr-123",
    "model": "text-moderation-007",
    "results": [
        {
            "flagged": False,
            "categories": {
                "sexual": False,
                "hate": False,
                "harassment": False,
                "self-harm": False,
                "sexual/minors": False,
                "hate/threatening": False,
                "violence/graphic": False,
                "violence": False,
                "harassment/threatening": False,
                "self-harm/intent": False,
                "self-harm/instructions": False,
            },
            "category_scores": {
                "sexual": 0.0001,
                "hate": 0.0002,
                "harassment": 0.0003,
                "self-harm": 0.0001,
                "sexual/minors": 0.00001,
                "hate/threatening": 0.00002,
                "violence/graphic": 0.0001,
                "violence": 0.0002,
                "harassment/threatening": 0.00003,
                "self-harm/intent": 0.00001,
                "self-harm/instructions": 0.00001,
            },
        }
    ],
}

SAMPLE_RESPONSE_FLAGGED: t.Dict[str, t.Any] = {
    "id": "modr-456",
    "model": "text-moderation-007",
    "results": [
        {
            "flagged": True,
            "categories": {
                "sexual": False,
                "hate": True,
                "harassment": True,
                "self-harm": False,
                "sexual/minors": False,
                "hate/threatening": False,
                "violence/graphic": False,
                "violence": False,
                "harassment/threatening": False,
                "self-harm/intent": False,
                "self-harm/instructions": False,
            },
            "category_scores": {
                "sexual": 0.01,
                "hate": 0.85,
                "harassment": 0.72,
                "self-harm": 0.001,
                "sexual/minors": 0.0001,
                "hate/threatening": 0.15,
                "violence/graphic": 0.02,
                "violence": 0.05,
                "harassment/threatening": 0.12,
                "self-harm/intent": 0.001,
                "self-harm/instructions": 0.0005,
            },
        }
    ],
}


class MockResponse:
    """Mock requests.Response object."""

    def __init__(self, json_data: t.Dict[str, t.Any], status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self) -> t.Dict[str, t.Any]:
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            from requests.exceptions import HTTPError
            raise HTTPError(f"HTTP Error: {self.status_code}")


def test_basic_interfaces() -> None:
    """Test basic interface methods."""
    assert OpenAIModerationClassifier.get_name() == "open_ai_moderation"
    assert OpenAIModerationClassifier.get_content_types() == [TextContent]


def test_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing API key raises appropriate error."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError):
        OpenAIModerationClassifier()


def test_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test credential discovery from environment variable."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-test-key")
    classifier = OpenAIModerationClassifier()
    assert classifier.api_key == "sk-env-test-key"


def test_api_key_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test explicit API key takes precedence."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
    classifier = OpenAIModerationClassifier(api_key="sk-explicit-key")
    assert classifier.api_key == "sk-explicit-key"


def test_parse_response_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test parsing a response with no flagged content."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    classifier = OpenAIModerationClassifier()
    result = classifier._parse_response(SAMPLE_RESPONSE_SAFE)

    assert not result.has_match
    assert len(result.labels) == 13

    for label, info in result.labels.items():
        assert not info.is_match
        assert info.score < 0.01


def test_parse_response_flagged(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test parsing a response with flagged content."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    classifier = OpenAIModerationClassifier()
    result = classifier._parse_response(SAMPLE_RESPONSE_FLAGGED)

    assert result.has_match
    assert len(result.positive_labels) == 2

    assert "hate" in result.positive_labels
    hate_info = result.labels["hate"]
    assert hate_info.is_match
    assert hate_info.score == 0.85
    assert hate_info.weight_str() == "85.00%"

    assert "harassment" in result.positive_labels
    harassment_info = result.labels["harassment"]
    assert harassment_info.is_match
    assert harassment_info.score == 0.72


def test_parse_response_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test parsing an empty response."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    classifier = OpenAIModerationClassifier()
    result = classifier._parse_response({"results": []})

    assert not result.has_match
    assert len(result.labels) == 0


def test_classification_result_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test string representation of classification result."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    classifier = OpenAIModerationClassifier()
    result = classifier._parse_response(SAMPLE_RESPONSE_FLAGGED)

    result_str = str(result)
    assert "hate" in result_str
    assert "harassment" in result_str
    assert "85.00%" in result_str
    assert "72.00%" in result_str


def test_classification_result_no_match_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test string representation when no matches."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    classifier = OpenAIModerationClassifier()
    result = classifier._parse_response(SAMPLE_RESPONSE_SAFE)

    assert str(result) == "None"


def test_classify_wrong_content_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that wrong content type raises ValueError."""
    from threatexchange.content_type.photo import PhotoContent

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    classifier = OpenAIModerationClassifier()

    with pytest.raises(ValueError) as exc_info:
        classifier.classify(PhotoContent, "test")

    assert "TextContent" in str(exc_info.value)


def test_classify_with_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test full classification flow with mocked HTTP."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def mock_post(*args, **kwargs):
        return MockResponse(SAMPLE_RESPONSE_FLAGGED)

    import requests
    monkeypatch.setattr(requests, "post", mock_post)

    classifier = OpenAIModerationClassifier()
    result = classifier.classify(TextContent, "some hateful text")

    assert result.has_match
    assert "hate" in result.positive_labels
    assert "harassment" in result.positive_labels


def test_classify_text_convenience(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the classify_text convenience method."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def mock_post(*args, **kwargs):
        return MockResponse(SAMPLE_RESPONSE_SAFE)

    import requests
    monkeypatch.setattr(requests, "post", mock_post)

    classifier = OpenAIModerationClassifier()
    result = classifier.classify_text("some safe text")

    assert not result.has_match


def test_moderation_classification_info() -> None:
    """Test ModerationClassificationInfo dataclass."""
    info = ModerationClassificationInfo(is_match=True, score=0.95)

    assert info.is_match
    assert info.score == 0.95
    assert info.weight_str() == "95.00%"
    assert str(info) == "95.00%"

    info_no_match = ModerationClassificationInfo(is_match=False, score=0.01)
    assert not info_no_match.is_match
    assert info_no_match.weight_str() == "1.00%"


def test_category_label_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that all OpenAI categories are mapped to labels."""
    expected_mappings = {
        "sexual": "sexual",
        "hate": "hate",
        "harassment": "harassment",
        "self-harm": "self_harm",
        "violence": "violence",
        "sexual/minors": "csam",
        "hate/threatening": "hate_threatening",
        "harassment/threatening": "harassment_threatening",
        "violence/graphic": "violence_graphic",
        "self-harm/intent": "self_harm_intent",
        "self-harm/instructions": "self_harm_instructions",
        "illicit": "illicit",
        "illicit/violent": "illicit_violent",
    }

    assert OpenAIModerationClassifier.CATEGORY_LABELS == expected_mappings
