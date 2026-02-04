#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""Classify command for content moderation."""

import argparse
import os
import sys
import json
import typing as t
from pathlib import Path

from threatexchange.cli.cli_config import CLISettings
from threatexchange.cli.exceptions import CommandError
from threatexchange.cli import command_base
from threatexchange.classifier.openai_moderation import (
    OpenAIModerationClassifier,
    MissingAPIKeyError,
)
from threatexchange.classifier.gpt_classifier import GPTClassifier

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


class ClassifyCommand(command_base.CommandWithSubcommands):
    """Classify content using moderation APIs."""

    _SUBCOMMANDS: t.ClassVar[t.List[t.Type[command_base.Command]]] = []

    @classmethod
    def get_name(cls) -> str:
        return "classify"

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: argparse.ArgumentParser) -> None:
        pass


class ModAPICommand(command_base.Command):
    """Classify text/images using OpenAI Moderation API. Requires OPENAI_API_KEY."""

    @classmethod
    def get_name(cls) -> str:
        return "modapi"

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: argparse.ArgumentParser) -> None:
        ap.add_argument("input", help="text, image path, image URL, or - for stdin")
        ap.add_argument("-t", "--text", help="text caption for image (multi-modal)")
        ap.add_argument(
            "-a", "--show-all", action="store_true", help="show all categories"
        )
        ap.add_argument("-m", "--model", default="omni-moderation-latest")
        ap.add_argument("-s", "--safeguard", action="store_true")
        ap.add_argument(
            "-p",
            "--policy",
            type=Path,
            default=(Path("threatexchange/classifier/policy/basic_policy.md")),
            help="Path to policy file (default: threatexchange/classifier/policy/basic_policy.md)",
        )

    def __init__(
        self,
        input: str,
        text: t.Optional[str] = None,
        show_all: bool = False,
        model: str = "omni-moderation-latest",
        safeguard: bool = False,
        policy: str = "threatexchange/classifier/policy/basic_policy.md",
    ):
        self.input = input
        self.text = text
        self.show_all = show_all
        self.model = model
        self.safeguard = safeguard
        self.policy = policy

    def execute(self, settings: CLISettings) -> None:
        # Auto-detect input type
        if self.input == "-":
            input_type, value = "text", sys.stdin.read()
        elif self.input.startswith(("http://", "https://")):
            input_type, value = "image", self.input
        else:
            ext = os.path.splitext(self.input)[1].lower()
            if ext in IMAGE_EXTENSIONS and os.path.isfile(self.input):
                input_type, value = "image", self.input
            elif os.path.isfile(self.input):
                with open(self.input) as f:
                    input_type, value = "text", f.read()
            else:
                input_type, value = "text", self.input

        try:
            if self.safeguard:
                classifier = GPTClassifier.from_env()
                gpt_result = classifier.classify(
                    content=self.input, policy=self.policy.read_text(encoding="utf-8")
                )
                print(json.dumps(gpt_result, indent=2, ensure_ascii=False, sort_keys=True))
                return
            else:
                classifier = OpenAIModerationClassifier(model=self.model)
        except MissingAPIKeyError as e:
            raise CommandError.user(str(e)) from e

        try:
            if input_type == "image" and self.text:
                result = classifier.classify_multi(value, self.text)
            elif input_type == "image":
                result = classifier.classify_image(value)
            else:
                result = classifier.classify_text(value)
        except Exception as e:
            raise CommandError.external_dependency(f"API error: {e}") from e

        if self.show_all:
            items = sorted(result.labels.items())
        else:
            items = sorted((l, i) for l, i in result.labels.items() if i.is_match)

        if not items:
            print("None")
        else:
            max_len = max(len(l) for l, _ in items)
            for label, info in items:
                flag = "FLAGGED" if info.is_match else ""
                print(f"  {label:<{max_len}}  {info.score:>6.2%}  {flag}")


ClassifyCommand._SUBCOMMANDS = [ModAPICommand]
