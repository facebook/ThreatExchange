#! /usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import json
import base64
import requests
import urllib3
import uuid
import time
import datetime
import dataclasses
import typing as t
from time import perf_counter
from urllib.parse import urljoin

from hmalib.scripts.common.utils import (
    HasherMatcherActionerAPI,
    get_terraform_outputs,
    get_auth_from_env,
)

from hmalib.common.classification_models import ClassificationLabel
from hmalib.common.configs.evaluator import ActionLabel, ActionRule
from hmalib.common.configs.actioner import (
    ActionPerformer,
    WebhookPostActionPerformer,
    CustomImplActionPerformer,
)


class DeployedInstanceClient:
    """
    Class around testing a deployed instance of HMA from Content Submission to Hash - Match - Action
    by checking that the expected values are found

    This class is structured in a way to have hma_script_utils.py avoid importing hmalib itself.
    """

    def __init__(
        self,
        api_url: str = "",
        api_token: str = "",
        api: HasherMatcherActionerAPI = None,
    ) -> None:
        if api:
            self.api = api
        else:
            if not api_token:
                raise ValueError(
                    "Test requires an api_token OR a client_id + refresh_token to function"
                )

            self.api = HasherMatcherActionerAPI(api_url, api_token)

    ### Start HMA API wrapper ###

    def create_dataset_config(
        self,
        privacy_group_id: str,
        privacy_group_name: str,
        description: str = "",
        matcher_active: bool = True,
        fetcher_active: bool = False,
        write_back: bool = False,
    ):
        self.api.create_dataset_config(
            privacy_group_id,
            privacy_group_name,
            description,
            matcher_active,
            fetcher_active,
            write_back,
        )

    def create_action(
        self,
        action_performer: ActionPerformer,
    ):
        return self.api.create_action(
            name=action_performer.name,
            config_subtype=action_performer.get_config_subtype(),
            fields={
                key: value
                for key, value in vars(action_performer).items()
                if key not in {"name", "config_subtype"}
            },
        )

    def delete_action(
        self,
        action_name: str,
    ):
        self.api.delete_action(action_name)

    def create_action_rule(
        self,
        action_rule: ActionRule,
    ):
        # Need to give the api a json like dict object (just like is used in aws)
        self.api.create_action_rule(action_rule.to_aws())

    def delete_action_rule(
        self,
        action_rule_name: str,
    ):
        self.api.delete_action_rule(action_rule_name)

    ### End HMA API wrapper ###

    ### Start Basic Test Methods  ####

    # Submit Content Test Set Up Defaults
    PRIVACY_GROUP_ID = "inria-holidays-test"
    ACTION_NAME = "SubmitContentTestActionWebhookPost"
    ACTION_CLASSIFICATION_LABEL = "holidays_jpg1_dataset"
    ACTION_RULE_PREFIX = "trigger-on-tag-"
    CUSTOM_ACTION_NAME = "SubmitContentTestCustomImplAction"

    def set_up_test(self, action_hook_url="http://httpstat.us/404"):
        """
        Set up/Create the following:
        - Dataset (Privacy Group Config)
        - Test Action (Action Performer Config)
        - Test Action Rule (Action Rule Config)

        Method is idempotent because the API will error when trying
        to create configs that already exist.

        """

        # Possible it already exists which is fine.
        self.create_dataset_config(
            privacy_group_id=self.PRIVACY_GROUP_ID,
            privacy_group_name="Test Sample Set",
        )

        self.set_up_test_actions(action_hook_url)

    def set_up_test_actions(self, action_hook_url="http://httpstat.us/404"):
        action_performer = WebhookPostActionPerformer(
            name=self.ACTION_NAME,
            url=action_hook_url,
            headers='{"this-is-a":"test-header"}',
        )

        self.create_action(
            action_performer=action_performer,
        )

        action_rule = ActionRule(
            name=f"{self.ACTION_RULE_PREFIX}{self.ACTION_CLASSIFICATION_LABEL}",
            action_label=ActionLabel(self.ACTION_NAME),
            must_have_labels=set(
                [
                    ClassificationLabel(self.ACTION_CLASSIFICATION_LABEL),
                ]
            ),
            must_not_have_labels=set(),
        )

        self.create_action_rule(
            action_rule=action_rule,
        )

    def set_up_custom_impl_test_actions(self, extension_name="ap_example_1"):
        action_performer = CustomImplActionPerformer(
            name=self.CUSTOM_ACTION_NAME,
            extension_name=extension_name,
            additional_kwargs={
                "defined_keyword_arg": "hello-custom-impl",
                "bonus_keyword": "here-is-where-it-put-other-values",
            },
        )

        self.create_action(
            action_performer=action_performer,
        )

        action_rule = ActionRule(
            name=f"{self.ACTION_RULE_PREFIX}{self.ACTION_CLASSIFICATION_LABEL}-custom",
            action_label=ActionLabel(self.CUSTOM_ACTION_NAME),
            must_have_labels=set(
                [
                    ClassificationLabel(self.ACTION_CLASSIFICATION_LABEL),
                ]
            ),
            must_not_have_labels=set(),
        )

        self.create_action_rule(
            action_rule=action_rule,
        )

    def clean_up_test(self):
        """
        Deletes specific action and action rules
        but does not delete the sample privacy group
        """
        self.api.delete_action_rule(
            f"{self.ACTION_RULE_PREFIX}{self.ACTION_CLASSIFICATION_LABEL}"
        )
        self.api.delete_action(self.ACTION_NAME)

    def clean_up_custom_impl_test(self):
        """
        Deletes specific action and action rules to custom impl
        """
        self.api.delete_action_rule(
            f"{self.ACTION_RULE_PREFIX}{self.ACTION_CLASSIFICATION_LABEL}-custom"
        )
        self.api.delete_action(self.CUSTOM_ACTION_NAME)

    def submit_test_content(
        self,
        content_id="submit_content_test_id_1",
        filepath="sample_data/b.jpg",
        additional_fields=[
            "this-is:a-test",
            "submitted-from:hma_client_lib.py",
        ],
    ):
        try:
            with open(filepath, "rb") as file:
                self.api.submit_via_upload_put_url(
                    content_id,
                    file,
                    additional_fields,
                )
        except (
            urllib3.exceptions.MaxRetryError,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException,
        ) as err:
            print("Error:", err)

    def submit_test_content_hash(
        self,
        content_id="submit_content_test_hash_id_1",
        content_type="photo",
        signal_value="f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22",  # pdq of "sample_data/b.jpg"
        signal_type="pdq",
        additional_fields=[
            "this-is:a-test-hash",
            "submitted-from:hma_client_lib.py",
        ],
    ):
        try:
            self.api.submit_via_hash(
                content_id=content_id,
                content_type=content_type,
                signal_value=signal_value,
                signal_type=signal_type,
                additional_fields=additional_fields,
            )
        except (
            urllib3.exceptions.MaxRetryError,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException,
        ) as err:
            print("Error:", err)

    def run_basic_test(self, wait_time_seconds=5, retry_limit=25, hash_submit=False):
        """
        Basic e2e (minus webhook listener) test:
        - Submit a piece of content expected to match/action
        - Check action history via the API for the content submitted
            - repeat until found or retry_limit hit
        """
        start_time = perf_counter()

        content_id = f"e2e-test-{datetime.date.today().isoformat()}-{str(uuid.uuid4())}"
        if hash_submit:
            self.submit_test_content_hash(content_id)
        else:
            self.submit_test_content(content_id)
        print(f"Submitted content_id {content_id}")

        print("Waiting for action history of submitted content_id")
        print(
            f"Checking every {wait_time_seconds} seconds; maximum tries = {retry_limit}"
        )
        while retry_limit and not len(self.api.get_content_action_history(content_id)):
            time.sleep(wait_time_seconds)
            retry_limit -= 0

        if retry_limit < 1:
            print("Error: hit retry limit on checking actions history")
        else:
            print("Success action event found in history!")
        print(f"Test completed in {int((perf_counter() - start_time))} seconds")


### End Basic Test Methods  ####


if __name__ == "__main__":
    # If you want manually test the lib, you can do so here:

    tf_outputs = get_terraform_outputs()
    api_url = tf_outputs["api_url"]
    token = get_auth_from_env(prompt_for_token=True)
    print(
        "This simple tests should take a little over 2 minutes to complete (due to sqs timeout).\n"
    )

    helper = DeployedInstanceClient(api_url, token)

    helper.set_up_test()
    # if you want to test a custom impl you can uncomment the followings line
    # Note: you will also need to make changes/create to settings.py
    # helper.set_up_custom_impl_test_actions()
    print("Added configurations to HMA instance for test")

    helper.run_basic_test()

    helper.clean_up_test()
    # helper.clean_up_custom_impl_test()
    print("Removed actions configurations used in test")
