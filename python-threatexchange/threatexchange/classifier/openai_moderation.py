# Copyright (c) Meta Platforms, Inc. and affiliates.

"""OpenAI Moderation API classifier."""

import base64
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
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.text import TextContent


class MissingAPIKeyError(Exception):
    """Raised when OPENAI_API_KEY is not set."""


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
        return [TextContent, PhotoContent]

    def classify(
        self, content_type: t.Type[content_base.ContentType], content_val: str
    ) -> ClassificationResult[ModerationClassificationInfo]:
        if content_type == TextContent:
            return self.classify_text(content_val)
        elif content_type == PhotoContent:
            return self.classify_image(content_val)
        else:
            raise ValueError(f"Unsupported content type: {content_type.get_name()}")

    def classify_text(
        self, text: str
    ) -> ClassificationResult[ModerationClassificationInfo]:
        """Classify text, returns result with labels."""
        return self._call_api(text=text)

    def classify_image(
        self, image: str
    ) -> ClassificationResult[ModerationClassificationInfo]:
        """Classify image from URL or local path."""
        return self._call_api(image=image)

    def classify_multi(
        self, image: str, text: str
    ) -> ClassificationResult[ModerationClassificationInfo]:
        """Classify image with text context."""
        return self._call_api(image=image, text=text)

    def _call_api(
        self, text: t.Optional[str] = None, image: t.Optional[str] = None
    ) -> ClassificationResult[ModerationClassificationInfo]:
        """Build input payload and call API."""
        if text and not image:
            payload: t.Dict[str, t.Any] = {"input": text, "model": self.model}
        else:
            parts: t.List[t.Dict[str, t.Any]] = []
            if text:
                parts.append({"type": "text", "text": text})
            if image:
                parts.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": self._image_to_url(image)},
                    }
                )
            payload = {"input": parts, "model": self.model}

        resp = requests.post(
            self.ENDPOINT,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        return self._parse_response(resp.json())

    def _image_to_url(self, image: str) -> str:
        """Convert image path or URL to API-compatible URL."""
        if image.startswith(("http://", "https://")):
            return image
        # Local file: base64 encode
        with open(image, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = image.lower().rsplit(".", 1)[-1]
        mime_types = {
            "jpg": "jpeg",
            "jpeg": "jpeg",
            "png": "png",
            "gif": "gif",
            "webp": "webp",
        }
        mime = mime_types.get(ext, "jpeg")
        return f"data:image/{mime};base64,{b64}"

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
