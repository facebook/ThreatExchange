#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""Chat command for content moderation."""

from __future__ import annotations

import argparse
import json
import os
import sys
import typing as t
from pathlib import Path

from threatexchange.chat.gpt_oss_safeguard import SafeguardClient
from threatexchange.cli import command_base
from threatexchange.cli.cli_config import CLISettings
from threatexchange.cli.exceptions import CommandError


class ChatCommand(command_base.Command):
    """Chat with gpt_oss_safeguard model."""

    def __init__(
        self,
        input: str,
        show_all: bool = False,
        model: str = "gpt-oss-safeguard",
        policy: str = "dataset/basic_policy.md",
    ):
        self.input = input
        self.show_all = show_all
        self.model = model
        self.policy = policy

    @classmethod
    def get_name(cls) -> str:
        return "chat"

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: argparse.ArgumentParser) -> None:
        ap.add_argument("input", help="text to chat, file path, or - for stdin")
        ap.add_argument(
            "-a", "--show-all", action="store_true", help="show all categories"
        )
        ap.add_argument("-m", "--model", default="gpt-oss-safeguard")
        ap.add_argument(
            "-p",
            "--policy",
            type=Path,
            default=(Path("threatexchange/chat/policy/basic_policy.md")),
            help="Path to policy file (default: threatexchange/chat/policy/basic_policy.md)",
        )

    def execute(self, settings: CLISettings) -> None:
        # Get text from stdin, file, or literal
        print(self.policy)
        if self.input == "-":
            text = sys.stdin.read()
        else:
            try:
                with open(self.input) as f:
                    text = f.read()
            except FileNotFoundError:
                text = self.input

        try:
            client = SafeguardClient.from_env()
            result = client.classify(
                content=self.input, policy=self.policy.read_text(encoding="utf-8")
            )
            print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        except Exception as e:
            raise CommandError.external_dependency(f"API error: {e}") from e
