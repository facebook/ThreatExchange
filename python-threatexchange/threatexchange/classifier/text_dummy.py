# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
A dummy classifier for testing and demonstration purposes.

This classifier performs simple text analysis based on character patterns,
such as detecting vowels, digits, email addresses, and URLs. It serves as
a reference implementation of the Classifier interface.
"""

import re
import typing as t
from dataclasses import dataclass

from threatexchange.classifier.classifier import (
    ClassificationInfo,
    ClassificationResult,
    Classifier,
)
from threatexchange.content_type import content_base
from threatexchange.content_type.text import TextContent


@dataclass
class WeightedClassificationInfo(ClassificationInfo):
    """ClassificationInfo with a numeric weight for confidence/proportion."""

    weight: float = 0.0

    def weight_str(self) -> str:
        """Return a human-friendly representation of the weight."""
        return f"{self.weight:.2f}"


class DummyTextClassifier(Classifier):
    """
    A toy classifier example that "classifies" text using simple heuristics.

    It is meant to demonstrate and test the interfaces.

    """

    # Regex patterns for detection
    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    URL_PATTERN = re.compile(r"https?://[^\s]+|www\.[^\s]+")

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[content_base.ContentType]]:
        """Return the content types this classifier can process."""
        return [TextContent]

    def classify_text(
        self, text: str
    ) -> ClassificationResult[WeightedClassificationInfo]:
        """Shortcut for longer form"""
        return self.classify(TextContent, text)

    def classify(
        self, content_type: t.Type[content_base.ContentType], content_val: str
    ) -> ClassificationResult[WeightedClassificationInfo]:
        """
        Classify text based on character patterns.

        Args:
            content_type: The type of content being classified.
            content_val: The text to classify.

        Returns:
            ClassificationResult with labels for detected patterns.
        """
        assert content_type == TextContent, "wrong content?"

        labels: t.Dict[str, WeightedClassificationInfo] = {}
        lower = content_val.lower()

        vowels = set("aeiou")
        vowel_count = sum(1 for c in lower if c in vowels)
        has_vowels = vowel_count > 0
        vowel_info = WeightedClassificationInfo(
            is_match=has_vowels,
            weight=vowel_count / len(content_val) if content_val else 0.0,
        )

        consonants = set("bcdfghjklmnpqrstvwxyz")
        consonant_count = sum(1 for c in lower if c in consonants)
        has_consonants = consonant_count > 0
        consonant_info = WeightedClassificationInfo(
            is_match=has_consonants,
            weight=consonant_count / len(content_val) if content_val else 0.0,
        )

        digit_count = sum(1 for c in content_val if c.isdigit())
        has_digits = digit_count > 0
        digit_info = WeightedClassificationInfo(
            is_match=has_digits,
            weight=digit_count / len(content_val) if content_val else 0.0,
        )

        email_matches = self.EMAIL_PATTERN.findall(content_val)
        has_email = len(email_matches) > 0
        email_info = WeightedClassificationInfo(
            is_match=has_email,
            weight=1.0 if has_email else 0.0,
        )

        url_matches = self.URL_PATTERN.findall(content_val)
        has_url = len(url_matches) > 0
        url_info = WeightedClassificationInfo(
            is_match=has_url,
            weight=1.0 if has_url else 0.0,
        )

        return ClassificationResult(
            {
                "vowel": vowel_info,
                "consonant": consonant_info,
                "digit": digit_info,
                "has_email": email_info,
                "has_url": url_info,
            }
        )
