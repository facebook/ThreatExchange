# Copyright (c) Meta Platforms, Inc. and affiliates.

"""Tests for the DummyTextClassifier."""

from threatexchange.classifier.classifier import (
    ClassificationInfo,
    ClassificationResult,
)
from threatexchange.classifier.text_dummy import DummyTextClassifier
from threatexchange.content_type.text import TextContent

CLASSIFIER = DummyTextClassifier()


def test_basic_ifaces() -> None:
    assert DummyTextClassifier.get_name() == "dummy_text"
    assert DummyTextClassifier.get_content_types() == [TextContent]


def test_classify_empty_string() -> None:
    result = CLASSIFIER.classify(TextContent, "")
    assert result == DummyTextClassifier.get_with_default_settings().classify(
        TextContent, ""
    )
    assert not result.has_match
    assert set(result.labels) == {
        "vowel",
        "consonant",
        "digit",
        "has_email",
        "has_url",
    }
    assert str(result) == "None"


def test_classify_with_vowels() -> None:
    # Our classifier doesn't think y is a vowel
    result = CLASSIFIER.classify_text("aeIOUy")
    assert result.has_match

    labels = result.labels
    assert labels["vowel"].is_match
    assert labels["vowel"].weight == 5 / 6
    assert labels["consonant"].is_match
    assert labels["consonant"].weight == 1 / 6

    assert str(result) == "vowel(0.83),consonant(0.17)"


def test_classify_email() -> None:
    result = CLASSIFIER.classify_text("Contact us at test@example.com for help")
    assert result.has_match

    labels = result.labels
    assert labels["has_email"].is_match
    assert labels["has_email"].weight == 1.0

    # Text without email should not match
    result_no_email = CLASSIFIER.classify_text("no email here")
    assert not result_no_email.labels["has_email"].is_match
    assert result_no_email.labels["has_email"].weight == 0.0


def test_classify_url() -> None:
    result = CLASSIFIER.classify_text("Visit https://example.com for more info")
    assert result.has_match

    labels = result.labels
    assert labels["has_url"].is_match
    assert labels["has_url"].weight == 1.0

    # Also test www. pattern
    result_www = CLASSIFIER.classify_text("Check out www.example.com")
    assert result_www.labels["has_url"].is_match
    assert result_www.labels["has_url"].weight == 1.0

    # Text without URL should not match
    result_no_url = CLASSIFIER.classify_text("no url here")
    assert not result_no_url.labels["has_url"].is_match
    assert result_no_url.labels["has_url"].weight == 0.0
