"""Minimal client for running an OSS Safeguard policy via an OpenAI-compatible API."""

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from openai import BadRequestError, OpenAI
from threatexchange.classifier.classifier import Classifier

DEFAULT_OPENAI_POLICY_MODEL = "osb-120b-ev3"


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _try_parse_json_object(text: str) -> dict[str, Any] | None:
    text = _strip_code_fences(text)
    try:
        val = json.loads(text)
        if isinstance(val, dict):
            return val
    except Exception:
        pass

    # Fallback: try to extract the first JSON object from a longer string.
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = text[start : end + 1]
    try:
        val = json.loads(candidate)
        if isinstance(val, dict):
            return val
    except Exception:
        return None
    return None


def _maybe_raise_helpful_model_error(exc: BadRequestError, *, model: str) -> None:
    body = getattr(exc, "body", None)
    if not isinstance(body, dict):
        return
    err = body.get("error")
    if not isinstance(err, dict):
        return

    code = err.get("code")
    message = err.get("message")
    if code != "model_not_found":
        return

    msg = str(message) if message else f"Model not found: {model!r}"
    raise RuntimeError(
        f"{msg}\n\n"
        f"This repo assumes the hackathon-provided API model {DEFAULT_OPENAI_POLICY_MODEL!r}.\n"
        "If you still see this error, confirm you have access to that model in your OpenAI project/org."
    ) from exc


@dataclass(frozen=True)
class GPTClassifier(Classifier):
    client: OpenAI
    model: str

    @classmethod
    def from_env(cls) -> "GPTClassifier":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY")

        model = DEFAULT_OPENAI_POLICY_MODEL

        client = OpenAI(
            api_key=api_key,
            organization=os.getenv("OPENAI_ORG_ID") or None,
            project=os.getenv("OPENAI_PROJECT_ID") or None,
        )
        return cls(client=client, model=model)  # type: ignore[arg-type]

    def get_content_types(self) -> str:
        return "text"

    def classify(self, *, content: str, policy: str) -> dict[str, Any]:
        """
        Returns:
          {
            "raw_text": "...",
            "parsed": { ... } | null
          }
        """
        raw_text = self._classify_via_responses(content=content, policy=policy)

        return {
            "raw_text": raw_text,
            "parsed": _try_parse_json_object(raw_text),
        }

    def _classify_via_responses(self, *, content: str, policy: str) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            # Harmony-style message roles: policy in developer message, content in user message.
            "input": [
                {"role": "developer", "content": policy},
                {"role": "user", "content": content},
            ],
        }
        try:
            response = self.client.responses.create(**kwargs)
        except BadRequestError as exc:
            _maybe_raise_helpful_model_error(exc, model=self.model)
            raise
        return (response.output_text or "").strip()
