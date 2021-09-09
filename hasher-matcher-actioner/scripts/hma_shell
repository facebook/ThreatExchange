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

import hma_script_utils
from hma_client_lib import DeployedInstanceClient

from listener import Listener
from submitter import Submitter

from hmalib.common.classification_models import ClassificationLabel
from hmalib.common.configs.evaluator import ActionLabel, ActionRule
from hmalib.common.configs.actioner import ActionPerformer, WebhookPostActionPerformer


class HMAShell(cmd.Cmd):
    intro = "Welcome! Type help or ? to list commands.\n"
    prompt = "> "

    def __init__(self, api_url: str, token: str):
        super(HMAShell, self).__init__()
        self.api = hma_script_utils.HasherMatcherActionerAPI(
            api_url,
            api_token=token,
        )

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Start a HMA Shell to intract with a deployed HMA instance."
    )
    parser.add_argument(
        "--access_token",
        help="access token to be used to authenticate request to HMA API",
        default="",
    )
    parser.add_argument(
        "--tf_output_file",
        help="Instead of using a python helper get_terraform_outputs, read output from a file\n e.g. via 'terraform -chdir=terraform output -json >> tf_outputs.json'",
    )

    args = parser.parse_args()

    if args.tf_output_file:
        tf_outputs = hma_script_utils.get_terraform_outputs_from_file(
            args.tf_output_file
        )
    else:
        tf_outputs = hma_script_utils.get_terraform_outputs()

    token = hma_script_utils.get_auth_from_env(
        token_default=args.access_token, prompt_for_token=True
    )

    api_url = tf_outputs["api_url"]["value"]

    HMAShell(api_url, token).cmdloop()
