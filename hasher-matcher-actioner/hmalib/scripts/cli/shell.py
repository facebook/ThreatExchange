#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Prototype of shell wrapper for HMA utils for interactive manual testings

```
python3 scripts/hma_shell --pwd <password-of-user-created-in-pool>
```

"""
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


class ShellCommand(base.Command):
    """
    Prototype of shell wrapper for HMA utils for interactive manual testings.
    """

    @classmethod
    def get_name(cls) -> str:
        """The display name of the command"""
        return "shell"

    @classmethod
    def get_help(cls) -> str:
        """The short help of the command"""
        return "open and interactive shell"

    def execute(self, api) -> None:
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

    def do_exit(self, arg):
        "Close the shell: exit"
        print("\nClosing Shell...\n")
        return True

    def _format_json_object_to_str(self, json_object):
        return json.dumps(json_object, indent=2)
