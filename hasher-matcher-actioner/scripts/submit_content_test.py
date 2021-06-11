#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import json
import base64
import requests
import dataclasses
import typing as t
from urllib.parse import urljoin
from script_utils import HasherMatcherActionerAPI

from hmalib.common.evaluator_models import Action, ActionRule
from hmalib.common.classification_models import Label, ActionLabel, ClassificationLabel
from hmalib.common.actioner_models import ActionPerformer, WebhookGetActionPerformer


class DeployedInstanceTestHelper:
    """
    Class around testing a deployed instance of HMA from Content Submission to Hash - Match - Action
    by checking that the expected values are found
    """

    SAMPLE_PG_ID = "inria-holidays-test"

    def __init__(
        self,
        api_url: str,
        api_token: str = "",
        client_id: str = None,
        refresh_token: str = None,
    ) -> None:
        if not api_token and (not client_id or not refresh_token):
            print(
                "Test requires an api_token OR a client_id + refresh_token to function"
            )
            exit(1)

        self.api = HasherMatcherActionerAPI(
            api_url, api_token, client_id, refresh_token
        )

    def _refresh_token(self):
        self.api._refresh_token()

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

    def create_action_rule(
        self,
        action_rule: ActionRule,
    ):
        # Need to give the api a json like dict object (just like is used in aws)
        self.api.create_action_rule(action_rule.to_aws())


def set_up(helper: DeployedInstanceTestHelper):
    helper.create_dataset_config(
        privacy_group_id=helper.SAMPLE_PG_ID,
        privacy_group_name="Holiday Sample Set",
    )

    action_performer = WebhookGetActionPerformer(
        name="TestActionWebhookGet",
        url="not_a_real_url",
        headers='{"this-is-a":"test-header"}',
    )

    helper.create_action(
        action_performer=action_performer,
    )

    action_rule = ActionRule(
        name="Trigger for holidays_jpg1_dataset tag 2",
        action_label=ActionLabel("TestActionWebhookGet"),
        must_have_labels=set(
            [
                ClassificationLabel("holidays_jpg1_dataset"),
            ]
        ),
        must_not_have_labels=set(),
    )

    helper.create_action_rule(
        action_rule=action_rule,
    )


def submit_content(helper: DeployedInstanceTestHelper):
    content_id = "submit_content_test_id_1"
    filepath = "sample_data/b.jpg"
    additional_fields = ["i-am:a-bridge", "this-is:a-test"]
    with open(filepath, "rb") as file:
        helper.api.send_single_submission_b64(
            content_id,
            file,
            additional_fields,
        )


def check_for_resulting_objects(helper: DeployedInstanceTestHelper):
    # TODO impl
    pass


if __name__ == "__main__":
    # If you want hard code tests for methods you can do so here:

    # Add init values for the api:
    # `os.environ.get(...)` will enable us pass values from `terraform output` in sh

    HMA_TOKEN = os.environ.get("HMA_TOKEN", "")
    # i.e. "https://<app-id>.execute-api.<region>.amazonaws.com/"
    HMA_API_URL = os.environ.get(
        "HMA_API_URL",
        "",
    )
    # See AWS Console: Cognito -> UserPools... -> App clients
    HMA_CLIENT_ID = os.environ.get(
        "HMA_CLIENT_ID",
        "",
    )
    # Can be created with dev certs `$ scripts/get_auth_token --refresh_token`
    HMA_REFRESH_TOKEN = os.environ.get("HMA_REFRESH_TOKEN", "")

    helper = DeployedInstanceTestHelper(
        HMA_API_URL, HMA_TOKEN, HMA_CLIENT_ID, HMA_REFRESH_TOKEN
    )
    helper._refresh_token()

    set_up(helper)

    submit_content(helper)

    # TODO
    check_for_resulting_objects(helper)
