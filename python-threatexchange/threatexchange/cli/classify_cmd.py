#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""Classify command for content moderation."""

import argparse
import sys
import typing as t

from threatexchange.cli.cli_config import CLISettings
from threatexchange.cli.exceptions import CommandError
from threatexchange.cli import command_base
from threatexchange.classifier.openai_moderation import (
    OpenAIModerationClassifier,
    MissingAPIKeyError,
)


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
    """Classify text using OpenAI Moderation API. Requires OPENAI_API_KEY."""

    @classmethod
    def get_name(cls) -> str:
        return "modapi"

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: argparse.ArgumentParser) -> None:
        ap.add_argument("input", help="text to classify, file path, or - for stdin")
        ap.add_argument("-a", "--show-all", action="store_true", help="show all categories")
        ap.add_argument("-m", "--model", default="omni-moderation-latest")

    def __init__(
        self,
        input: str,
        show_all: bool = False,
        model: str = "omni-moderation-latest",
    ):
        self.input = input
        self.show_all = show_all
        self.model = model

    def execute(self, settings: CLISettings) -> None:
        # Get text from stdin, file, or literal
        if self.input == "-":
            text = sys.stdin.read()
        else:
            try:
                with open(self.input) as f:
                    text = f.read()
            except FileNotFoundError:
                text = self.input

        try:
            classifier = OpenAIModerationClassifier(model=self.model)
        except MissingAPIKeyError as e:
            raise CommandError.user(str(e)) from e

        try:
            result = classifier.classify_text(text)
        except Exception as e:
            raise CommandError.external_dependency(f"API error: {e}") from e

        if self.show_all:
            parts = [
                f"{label}({info.score:.0%},{'+' if info.is_match else '-'})"
                for label, info in sorted(result.labels.items())
            ]
            print(",".join(parts) or "None")
        else:
            flagged = [
                f"{label}({info.score:.0%})"
                for label, info in sorted(result.labels.items())
                if info.is_match
            ]
            print(",".join(flagged) or "None")


ClassifyCommand._SUBCOMMANDS = [ModAPICommand]
