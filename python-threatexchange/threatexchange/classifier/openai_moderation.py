# Copyright (c) Meta Platforms, Inc. and affiliates.

"""OpenAI Moderation API classifier."""

import os
import typing as t
from dataclasses import dataclass

import requests

from threatexchange.classifier.classifier import (
    ClassificationInfo,
    ClassificationResult,
    Classifier,
)
from threatexchange.content_type import content_base
from threatexchange.content_type.text import TextContent


class MissingAPIKeyError(Exception):
    """Raised when OPENAI_API_KEY is not set."""

    pass


@dataclass
class ModerationClassificationInfo(ClassificationInfo):
    """Classification info with confidence score."""

    score: float = 0.0

    def weight_str(self) -> str:
        return f"{self.score:.2%}"


class OpenAIModerationClassifier(Classifier):
    """Classifies text using OpenAI's Moderation API."""

    ENDPOINT = "https://api.openai.com/v1/moderations"
    DEFAULT_MODEL = "omni-moderation-latest"

    CATEGORY_LABELS: t.ClassVar[t.Dict[str, str]] = {
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

    def __init__(self, model: t.Optional[str] = None, api_key: t.Optional[str] = None):
        self.model = model or self.DEFAULT_MODEL
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise MissingAPIKeyError("Set OPENAI_API_KEY environment variable")

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[content_base.ContentType]]:
        return [TextContent]

    def classify(
        self, content_type: t.Type[content_base.ContentType], content_val: str
    ) -> ClassificationResult[ModerationClassificationInfo]:
        if content_type != TextContent:
            raise ValueError(f"Only supports TextContent, got {content_type.get_name()}")
        return self.classify_text(content_val)

    def classify_text(self, text: str) -> ClassificationResult[ModerationClassificationInfo]:
        """Classify text, returns result with labels."""
        resp = requests.post(
            self.ENDPOINT,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"input": text, "model": self.model},
            timeout=30,
        )
        resp.raise_for_status()
        return self._parse_response(resp.json())

    def _parse_response(
        self, data: t.Dict[str, t.Any]
    ) -> ClassificationResult[ModerationClassificationInfo]:
        labels: t.Dict[str, ModerationClassificationInfo] = {}
        results = data.get("results", [])
        if not results:
            return ClassificationResult(labels)

        r = results[0]
        cats, scores = r.get("categories", {}), r.get("category_scores", {})
        for cat, label in self.CATEGORY_LABELS.items():
            labels[label] = ModerationClassificationInfo(
                is_match=cats.get(cat, False),
                score=scores.get(cat, 0.0),
            )
        return ClassificationResult(labels)
