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
from threatexchange.classifier.safeguard.gpt_classifier import GPTClassifier


class ClassifyCommand(command_base.CommandWithSubcommands):
    """Classify content using moderation APIs."""

    _SUBCOMMANDS: t.List[t.Type[command_base.Command]] = []

    @classmethod
    def get_name(cls) -> str:
        return "classify"

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: argparse.ArgumentParser) -> None:
        pass


class ClassifyTextCommand(command_base.Command):
    """Classify text content using moderation APIs. Requires OPENAI_API_KEY."""

    @classmethod
    def get_name(cls) -> str:
        return "text"

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: argparse.ArgumentParser) -> None:
        ap.add_argument(
            "input",
            help="text string, file path, or - for stdin",
        )
        ap.add_argument(
            "--mod-api",
            action="store_true",
            help="use OpenAI Moderation API (default)",
        )
        ap.add_argument(
            "-a", "--show-all", action="store_true", help="show all categories"
        )
        ap.add_argument("-s", "--safeguard", action="store_true")
        ap.add_argument(
            "-p",
            "--policy",
            type=Path,
            default=(
                Path("threatexchange/classifier/safeguard/policy/basic_policy.md")
            ),
            help="Path to policy file (default: threatexchange/classifier/safeguard/policy/basic_policy.md)",
        )
        ap.add_argument(
            "-m",
            "--model",
            default="omni-moderation-latest",
            help="model to use (default: omni-moderation-latest)",
        )

    def __init__(
        self,
        input: str,
        mod_api: bool = False,
        show_all: bool = False,
        model: str = "omni-moderation-latest",
        safeguard: bool = False,
        policy: str = "threatexchange/classifier/safeguard/policy/basic_policy.md",
    ):
        self.input = input
        self.mod_api = mod_api
        self.show_all = show_all
        self.model = model
        self.safeguard = safeguard
        self.policy = policy

    def execute(self, settings: CLISettings) -> None:
        # Resolve text input
        if self.input == "-":
            text = sys.stdin.read()
        elif os.path.isfile(self.input):
            with open(self.input) as f:
                text = f.read()
        else:
            text = self.input

        # Default to mod-api if no API flag specified
        # (currently only mod-api is supported)
        try:
            if self.safeguard:
                classifier = GPTClassifier.from_env()
                gpt_result = classifier.classify(
                    content=self.input, policy=self.policy.read_text(encoding="utf-8")
                )
                print(
                    json.dumps(gpt_result, indent=2, ensure_ascii=False, sort_keys=True)
                )
                return
            else:
                classifier = OpenAIModerationClassifier(model=self.model)
        except MissingAPIKeyError as e:
            raise CommandError.user(str(e)) from e

        try:
            result = classifier.classify_text(text)
        except Exception as e:
            raise CommandError.external_dependency(f"API error: {e}") from e

        _print_classification_result(result, self.show_all)


class ClassifyImageCommand(command_base.Command):
    """Classify image content using moderation APIs."""

    @classmethod
    def get_name(cls) -> str:
        return "image"

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: argparse.ArgumentParser) -> None:
        ap.add_argument(
            "input",
            help="image file path or URL",
        )
        ap.add_argument(
            "--mod-api",
            action="store_true",
            help="use OpenAI Moderation API (default)",
        )
        ap.add_argument(
            "-a", "--show-all", action="store_true", help="show all categories"
        )
        ap.add_argument(
            "-m",
            "--model",
            default="omni-moderation-latest",
            help="model to use (default: omni-moderation-latest)",
        )

    def __init__(
        self,
        input: str,
        mod_api: bool = False,
        show_all: bool = False,
        model: str = "omni-moderation-latest",
    ):
        self.input = input
        self.mod_api = mod_api
        self.show_all = show_all
        self.model = model

    def execute(self, settings: CLISettings) -> None:
        raise CommandError.user("Image classification is not implemented yet")


class ClassifyHybridCommand(command_base.Command):
    """Classify image + text together (multi-modal) using moderation APIs."""

    @classmethod
    def get_name(cls) -> str:
        return "hybrid"

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: argparse.ArgumentParser) -> None:
        ap.add_argument(
            "image",
            help="image file path or URL",
        )
        ap.add_argument(
            "text",
            help="text caption or description for the image",
        )
        ap.add_argument(
            "--mod-api",
            action="store_true",
            help="use OpenAI Moderation API (default)",
        )
        ap.add_argument(
            "-a", "--show-all", action="store_true", help="show all categories"
        )
        ap.add_argument(
            "-m",
            "--model",
            default="omni-moderation-latest",
            help="model to use (default: omni-moderation-latest)",
        )

    def __init__(
        self,
        image: str,
        text: str,
        mod_api: bool = False,
        show_all: bool = False,
        model: str = "omni-moderation-latest",
    ):
        self.image = image
        self.text = text
        self.mod_api = mod_api
        self.show_all = show_all
        self.model = model

    def execute(self, settings: CLISettings) -> None:
        raise CommandError.user("Hybrid classification is not implemented yet")


def _print_classification_result(result, show_all: bool) -> None:
    """Print classification results in a formatted table."""
    if show_all:
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


ClassifyCommand._SUBCOMMANDS = [
    ClassifyTextCommand,
    ClassifyImageCommand,
    ClassifyHybridCommand,
]
