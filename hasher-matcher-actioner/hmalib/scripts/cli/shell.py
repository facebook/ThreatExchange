#! /usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import cmd
import os
import argparse
import time
import threading
import uuid
import json
import datetime
from dataclasses import dataclass
import numpy as np
import pandas as pd
import typing as t

import hmalib.scripts.common.utils as utils
import hmalib.scripts.cli.command_base as base

from hmalib.scripts.common.client_lib import DeployedInstanceClient
from hmalib.scripts.common.listener import Listener
from hmalib.scripts.common.submitter import Submitter

from hmalib.common.classification_models import ClassificationLabel
from hmalib.common.configs.evaluator import ActionLabel, ActionRule
from hmalib.common.configs.actioner import ActionPerformer, WebhookPostActionPerformer


class ShellCommand(base.Command, base.NeedsAPIAccess):
    """
    Prototype shell using HMA utils to interact via the API.
    """

    @classmethod
    def init_argparse(cls, ap: argparse.ArgumentParser) -> None:
        ap.add_argument(
            "--cmd",
            help=f"run one command and exit. Options: {HMAShell.get_commands()}",
        )

    def __init__(
        self,
        cmd: str = "",
    ) -> None:
        self.cmd = cmd

    @classmethod
    def get_name(cls) -> str:
        return "shell"

    @classmethod
    def get_help(cls) -> str:
        return "open interactive shell OR run single command (via --cmd)"

    def execute(self, api: utils.HasherMatcherActionerAPI) -> None:
        if self.cmd:
            HMAShell(api).onecmd(self.cmd)
        else:
            HMAShell(api).cmdloop()


class HMAShell(cmd.Cmd):
    intro = "Welcome! Type help or ? to list commands.\n"
    prompt = "> "

    def __init__(self, api: utils.HasherMatcherActionerAPI):
        super(HMAShell, self).__init__()
        self.api = api

    # Query Commands
    def do_dataset_configs(self, arg):
        "Get list of current dataset configs: dataset_configs"
        print(self._format_json_object_to_str(self.api.get_dataset_configs()))

    def do_matches(self, arg):
        "Get list of current match objects: matches"
        matches = self.api.get_all_matches()
        print(self._format_json_object_to_str(matches))
        print(f"Total Matches: {len(matches)}")

    def do_actions(self, arg):
        "Get list of current actions: actions"
        print(self._format_json_object_to_str(self.api.get_actions()))

    def do_action_rules(self, arg):
        "Get list of current action_rules: action_rules"
        print(self._format_json_object_to_str(self.api.get_action_rules()))

    # Query Content Commands
    def do_hash_details_for_id(self, arg):
        "Get hash_details for content id: hash_details_for_id <content id>"
        print(self._format_json_object_to_str(self.api.get_content_hash_details(arg)))

    def do_matches_for_id(self, arg):
        "Get matches for content id: matches_for_id <content id>"
        print(self._format_json_object_to_str(self.api.get_content_matches(arg)))

    def do_matches_for_hash(self, arg):
        "Get matches for a hash: matches_for_hash [pdq|video_md5] <hash>"
        arg_lst = arg.split()
        signal_type = arg_lst[0]
        hash_val = arg_lst[1]
        print(
            self._format_json_object_to_str(
                self.api.get_matches_for_hash(signal_type, hash_val)
            )
        )

    def do_action_history_for_id(self, arg):
        "Get action_history for content id: action_history_for_id <content id>"
        print(self._format_json_object_to_str(self.api.get_content_action_history(arg)))

    # Create Commands
    # Submit Commands
    # TODO

    # Test Commands
    def do_run_basic_test(self, arg):
        "Set up, run, and cleanup a basic test: run_basic_test"
        DeployedInstanceClient(api=self.api).run_basic_test()

    # Utility commands

    def do_quit(self, arg):
        "Close the shell: quit"
        print("\nClosing Shell...\n")
        return True

    def _format_json_object_to_str(self, json_object):
        return json.dumps(json_object, indent=2)

    @classmethod
    def get_commands(cls):
        names = dir(cls)
        cmds = []
        names.sort()
        # There can be duplicates if routines overridden
        prevname = ""
        for name in names:
            if name[:3] == "do_":
                if name == prevname:
                    continue
                prevname = name
                cmd = name[3:]
                cmds.append(cmd)
        return cmds
