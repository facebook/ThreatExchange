#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import json
import base64
import requests
import urllib3
import time
import dataclasses
import typing as t
from urllib.parse import urljoin

from script_utils import HasherMatcherActionerAPI
from listener import Listener

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
        self.listener = Listener()

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

    def create_action_rule(
        self,
        action_rule: ActionRule,
    ):
        # Need to give the api a json like dict object (just like is used in aws)
        self.api.create_action_rule(action_rule.to_aws())

    ### End HMA API wrapper ###

    ### Start Basic Test Methods  ####

    def set_up_test(self, hostname: str, port: int):
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
            privacy_group_id="inria-holidays-test",
            privacy_group_name="Holiday Sample Set",
        )

        # ToDo These actions should be cleaned up with clean_up_basic_test
        action_performer = WebhookPostActionPerformer(
            name="SubmitContentTestActionWebhookPost",
            url=f"http://{hostname}:{port}",
            headers='{"this-is-a":"test-header"}',
        )

        self.create_action(
            action_performer=action_performer,
        )

        action_rule = ActionRule(
            name="trigger-on-tag-holidays_jpg1_dataset",
            action_label=ActionLabel("SubmitContentTestActionWebhookPost"),
            must_have_labels=set(
                [
                    ClassificationLabel("holidays_jpg1_dataset"),
                ]
            ),
            must_not_have_labels=set(),
        )

        self.create_action_rule(
            action_rule=action_rule,
        )

    def clean_up_test(self, hostname: str, port: int):
        """
        Deletes specific action and action rules
        """
        raise NotImplementedError

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

    def start_listening_for_action_post_requests(self, hostname: str, port: int):
        self.listener.start_listening(hostname, port)

    def stop_listening_for_action_post_requests(self):
        self.listener.stop_listening()

    def get_post_count_so_far_requests(self) -> int:
        return self.listener.get_post_request_count()

    def run_basic_test_with_webhook_listener(self, hostname: str, port: int):
        """
        As the test suggests it is pretty basic:
        - spin up a webserver to listen for a webhook
        - submits a piece of content we expect to match
        - every 5 second ask the webserver if it has received a post request
        - if a post request was received shutdown server and return

        Test needs to be run from a computer (likely ec2), that can bind and then receive request at
        (external) 'hostname' and 'port'
        """
        self.start_listening_for_action_post_requests(hostname, port)

        self.submit_test_content()

        post_counter = 0
        while post_counter < 1:
            time.sleep(10)
            post_counter = self.get_post_count_so_far_requests()

        time.sleep(5)
        self.stop_listening_for_action_post_requests()


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

    hostname = os.environ.get(
        "LISTENER_EXTERNAL_HOSTNAME",
        "localhost",
    )

    port = int(
        os.environ.get(
            "LISTENER_PORT",
            "8080",
        )
    )

    helper = DeployedInstanceTestHelper(api_url, token, client_id, refresh_token)

    if refresh_token and client_id:
        helper.refresh_api_token()

    helper.set_up_test(hostname, port)

    helper.run_basic_test_with_webhook_listener(hostname, port)
