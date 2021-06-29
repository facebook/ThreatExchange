#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

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

from script_utils import HasherMatcherActionerAPI

from hmalib.common.evaluator_models import ActionRule
from hmalib.common.classification_models import ActionLabel, ClassificationLabel
from hmalib.common.actioner_models import ActionPerformer, WebhookPostActionPerformer


class DeployedInstanceTestHelper:
    """
    Class around testing a deployed instance of HMA from Content Submission to Hash - Match - Action
    by checking that the expected values are found

    This class is structed in a way to have script_utils.py avoid importing hmalib itself.
    """

    def __init__(
        self,
        api_url: str,
        api_token: str = "",
        client_id: str = None,
        refresh_token: str = None,
    ) -> None:
        if not api_token and (not client_id or not refresh_token):
            raise ValueError(
                "Test requires an api_token OR a client_id + refresh_token to function"
            )

        self.api = HasherMatcherActionerAPI(
            api_url, api_token, client_id, refresh_token
        )

    def refresh_api_token(self):
        """
        Manually refresh api's token
        TODO Make staleness of the token an internal matter for the API class to handle.
        """
        self.api._refresh_token()

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
        self.api.create_action(
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

    def clean_up_test(self):
        """
        Deletes specific action and action rules
        but does not delete the sample privacy group
        """
        self.api.delete_action_rule(
            f"{self.ACTION_RULE_PREFIX}{self.ACTION_CLASSIFICATION_LABEL}"
        )
        self.api.delete_action(self.ACTION_NAME)

    def submit_test_content(
        self,
        content_id="submit_content_test_id_1",
        filepath="sample_data/b.jpg",
        additional_fields=[
            "this-is:a-test",
            "submitted-from:submit_content_test.py",
        ],
    ):
        try:
            with open(filepath, "rb") as file:
                self.api.send_single_submission_url(
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

    def run_basic_test(self, wait_time_seconds=5, retry_limit=25):
        """
        Basic e2e (minus webhook listener) test:
        - Create the configurations needed :
        - Submit a piece of content expected to match/action
        - Check action history via the API for the content submitted
            - repeat until found or retry_limit hit
        """
        start_time = perf_counter()

        self.set_up_test()
        print("Added configurations to HMA instance for test")

        content_id = f"e2e-test-{datetime.date.today().isoformat()}-{str(uuid.uuid4())}"
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
        self.clean_up_test()
        print("Removed actions configurations used in test")
        print(f"Test completed in {int((perf_counter() - start_time))} seconds")


### End Basic Test Methods  ####


if __name__ == "__main__":
    # If you want manually test the lib, you can do so here:

    # i.e. "https://<app-id>.execute-api.<region>.amazonaws.com/"
    api_url = os.environ.get(
        "HMA_API_URL",
        "",
    )

    token = os.environ.get(
        "HMA_TOKEN",
        "",
    )

    # See AWS Console: Cognito -> UserPools... -> App clients
    client_id = os.environ.get(
        "HMA_COGNITO_USER_POOL_CLIENT_ID",
        "",
    )

    # Can be created with dev certs `$ scripts/get_auth_token --refresh_token`
    refresh_token = os.environ.get(
        "HMA_REFRESH_TOKEN",
        "",
    )

    helper = DeployedInstanceTestHelper(api_url, token, client_id, refresh_token)

    if refresh_token and client_id:
        helper.refresh_api_token()

    helper.set_up_test()

    helper.run_basic_test()

    helper.clean_up_test()
