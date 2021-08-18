#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Utilities for hma scripts
"""

import os
import json
import base64
import requests
import boto3
import subprocess
import functools
import typing as t
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin
from botocore.exceptions import ClientError

# Defaults to override values in tf outputs or ENV
API_URL = ""
TOKEN = ""
REFRESH_TOKEN = ""
CLIENT_ID = ""
USER = ""
PWD = ""


class HasherMatcherActionerAPI:
    """
    Class for interfacing with a subset HMA API endpoints in python scripts.
    Supports future and existing storm, soak, and smoke test as well as being
    useful for debuging outside of the HMA UI and AWS Console.

    See hmalib/lambdas/api/
    """

    def __init__(
        self,
        api_url: str,
        api_token: str,
        client_id: str = None,
        refresh_token: str = None,
        transport_adapter: HTTPAdapter = None,
    ) -> None:
        self.api_url = api_url
        self.client_id = client_id
        self.refresh_token = refresh_token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "content-type": "application/json",
                "authorization": api_token,
            }
        )
        if transport_adapter:
            self.session.mount(api_url, transport_adapter)

    def _refresh_token(self):
        """
        IdToken has a default ttl of 60 minutes
        RefreshToken as a default ttl of 30 days
        Only works in boto3 is install and optional values are set.
        """
        if not self.client_id or not self.refresh_token:
            raise ValueError("Refresh Token and/or Client ID Missing")

        client = boto3.client("cognito-idp", region_name="us-east-1")

        resp = client.initiate_auth(
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": self.refresh_token},
            ClientId=self.client_id,
        )
        api_token = resp["AuthenticationResult"]["IdToken"]
        self.session.headers["authorization"] = api_token
        return api_token

    def _get_request_url(self, api_path: str) -> str:
        return urljoin(self.api_url, api_path)

    def get(self, api_path: str = ""):
        response = self.session.get(self._get_request_url(api_path))
        return response.json()

    def get_all_matches(self, api_path: str = "/matches/"):
        response = self.session.get(self._get_request_url(api_path))
        response.raise_for_status()
        return response.json().get("match_summaries", [])

    def submit_via_encoded_bytes(
        self,
        content_id: str,
        b64_file_contents: str,
        additional_fields: t.List[str] = [],
    ):
        payload = {
            "content_id": content_id,
            "content_type": "photo",
            "additional_fields": additional_fields,
            "content_bytes": b64_file_contents,
        }
        api_path: str = "/submit/bytes/"
        response = self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode("utf-8"),
        )
        response.raise_for_status()

    def submit_via_upload_put_url(
        self,
        content_id: str,
        file: t.BinaryIO,
        additional_fields: t.List[str] = [],
    ):
        payload = {
            "content_id": content_id,
            "content_type": "photo",
            "additional_fields": additional_fields,
            "file_type": "image/jpeg",
        }
        api_path: str = "/submit/post_url/"
        response = self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )
        response.raise_for_status()

        response_json = response.json()

        put_response = requests.put(
            response_json["presigned_url"],
            data=file,
            headers={"content-type": "image/jpeg"},
        )
        put_response.raise_for_status()

    def submit_via_external_url(
        self,
        url: str,
        content_id: str,
        additional_fields: t.List[str] = [],
    ):
        """
        Distinct from submit_via_upload_put_url(), It uses the URL only path
        and bypasses s3 completely.
        """
        payload = {
            "content_id": content_id,
            "content_type": "photo",
            "additional_fields": additional_fields,
            "content_url": url,
        }
        api_path: str = "/submit/url/"
        response = self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )
        response.raise_for_status()

    def submit_hash(
        self,
        content_id: str,
        signal_value: str,
        signal_type: str = "pdq",
        content_type: str = "photo",
        url="",
        additional_fields: t.List[str] = [],
    ):
        """
        Submit hash directy
        """
        payload = {
            "content_id": content_id,
            "content_type": content_type,
            "additional_fields": additional_fields,
            "signal_value": signal_value,
            "signal_type": signal_type,
            "content_url": url,
        }
        api_path: str = "/submit/hash/"
        response = self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )
        response.raise_for_status()

    def get_content_hash_details(
        self,
        content_id: str,
        api_path: str = "/content/hash/",
    ):
        return self.session.get(
            self._get_request_url(api_path),
            params={"content_id": content_id},
        ).json()

    def get_content_action_history(
        self,
        content_id: str,
        api_path: str = "/content/action-history/",
    ):
        response = self.session.get(
            self._get_request_url(api_path),
            params={"content_id": content_id},
        )
        return response.json().get("action_history", [])

    def get_content_matches(
        self,
        content_id: str,
        api_path: str = "/matches/match/",
    ):
        response = self.session.get(
            self._get_request_url(api_path),
            params={"content_id": content_id},
        )
        return response.json().get("match_details", [])

    def get_dataset_configs(
        self,
        api_path: str = "/datasets/",
    ):
        response = self.session.get(self._get_request_url(api_path))
        return response.json().get("threat_exchange_datasets", [])

    def create_dataset_config(
        self,
        privacy_group_id: str,
        privacy_group_name: str,
        description: str = "",
        matcher_active: bool = True,
        fetcher_active: bool = False,
        write_back: bool = False,
        api_path: str = "/datasets/create",
    ):
        payload = {
            "privacy_group_id": privacy_group_id,
            "privacy_group_name": privacy_group_name,
            "description": description,
            "fetcher_active": fetcher_active,
            "matcher_active": matcher_active,
            "write_back": write_back,
        }
        self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )

    def get_actions(
        self,
        api_path: str = "/actions/",
    ):
        response = self.session.get(self._get_request_url(api_path))
        return response.json().get("actions_response", [])

    def create_action(
        self,
        name: str,
        config_subtype: str,
        fields: t.Dict[str, t.Any],
        api_path: str = "/actions/",
    ):
        payload = {
            "name": name,
            "config_subtype": config_subtype,
            "fields": fields,
        }
        self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )

    def delete_action(
        self,
        action_name: str,
        api_path: str = "/actions/",
    ):
        self.session.delete(self._get_request_url(api_path + action_name))

    def get_action_rules(
        self,
        api_path: str = "/action-rules/",
    ):
        response = self.session.get(self._get_request_url(api_path))
        return response.json().get("action_rules", [])

    def create_action_rule(
        self,
        action_rule: t.Any,
        api_path: str = "/action-rules/",
    ):
        payload = {
            "action_rule": action_rule,
        }
        self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )

    def delete_action_rule(
        self,
        action_rule_name: str,
        api_path: str = "/action-rules/",
    ):
        self.session.delete(self._get_request_url(api_path + action_rule_name))


def get_terraform_outputs(
    directory: str = "/workspaces/ThreatExchange/hasher-matcher-actioner/terraform",
):
    cmd = ["terraform"]
    cmd.extend(["output", "-json"])
    out = subprocess.check_output(cmd, cwd=directory)
    return json.loads(out)


def get_terraform_outputs_from_file(
    path: str = "/workspaces/ThreatExchange/hasher-matcher-actioner/tmp.out",
):
    with open(path) as f:
        return json.loads(f.read())


@functools.lru_cache(maxsize=None)
def _get_cognito_client():
    return boto3.client("cognito-idp")


def get_token(
    username: str,
    pwd: str,
    pool_id: str,
    client_id: str,
):
    resp = _get_cognito_client().admin_initiate_auth(
        AuthFlow="ADMIN_USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": username, "PASSWORD": pwd},
        UserPoolId=pool_id,
        ClientId=client_id,
    )
    return resp


def create_user(
    username: str,
    email: str,
    pwd: str,
    pool_id: str,
    client_id: str,
):
    _get_cognito_client().admin_create_user(
        UserPoolId=pool_id,
        Username=username,
        UserAttributes=[
            {"Name": "email_verified", "Value": "True"},
            {"Name": "email", "Value": email},
        ],
        ForceAliasCreation=False,
        MessageAction="SUPPRESS",
    )
    _get_cognito_client().admin_set_user_password(
        UserPoolId=pool_id,
        Username=username,
        Password=pwd,
        Permanent=True,
    )


def delete_user(
    username: str,
    pwd: str,
    pool_id: str,
    client_id: str,
):
    try:
        resp = _get_cognito_client().admin_delete_user(
            UserPoolId=pool_id,
            Username=username,
        )
    except ClientError as err:
        # if the user is not found.
        pass


def get_default_user_name(prefix: str):
    return f"{prefix}testuser"


def get_auth_from_env(
    tf_outputs: t.Dict,
    token_default: str = TOKEN,
    refresh_token_default: str = REFRESH_TOKEN,
    pwd_override: str = PWD,
    client_id_override: str = CLIENT_ID,
    user_override: str = USER,
    prompt_for_pwd: bool = False,
):

    # Can be created with dev certs: `export HMA_TOKEN=$(./scripts/get_auth_token --pwd <pwd>)`
    token = os.environ.get(
        "HMA_TOKEN",
        token_default,
    )

    # Can be created with dev certs: `export HMA_REFRESH_TOKEN=$(./scripts/get_auth_token --refresh_token --pwd <pwd>)`
    refresh_token = os.environ.get(
        "HMA_REFRESH_TOKEN",
        refresh_token_default,
    )

    # Password that if found in ENV can be used to get a token
    pwd = pwd_override or os.environ.get(
        "HMA_USER_PWD",
        "",
    )

    client_id = client_id_override or tf_outputs["cognito_user_pool_client_id"]["value"]

    if not token and not refresh_token:
        user = user_override or get_default_user_name(tf_outputs["prefix"]["value"])
        if not pwd:
            if prompt_for_pwd:
                print(f"Needs a password for user: {user} to authenticate.")
                pwd = input("Enter password: ")
            else:
                print(
                    "Authentication requires at least one of HMA_TOKEN, HMA_REFRESH_TOKEN, or HMA_USER_PWD be present in ENV."
                )
                print(
                    "You can also hard code these values and others in scripts/hma_script_utils.py if you are trying to set outside of our development ENV (e.g. on an ec2 instance)."
                )
                print(
                    "See: `script/get_auth_token` these values are associated with a user if you don't have one you can create one with the script as well."
                )
                exit()

        pool_id = tf_outputs["cognito_user_pool_id"]["value"]
        resp = get_token(user, pwd, pool_id, client_id)
        token = resp["AuthenticationResult"]["IdToken"]
        refresh_token = resp["AuthenticationResult"]["RefreshToken"]

    return (token, refresh_token, client_id)


if __name__ == "__main__":
    # If you want hard code tests for methods you can do so here:

    # Testing HasherMatcherActionerAPI
    #   Since the API requries a deployed instance the majority of
    #   testing needs to be done manually. See below.
    print("Manual Test of API Request Methods:")

    tf_outputs = get_terraform_outputs()

    api_url = tf_outputs["api_url"]["value"]

    token, refresh_token, client_id = get_auth_from_env(tf_outputs)

    api = HasherMatcherActionerAPI(
        api_url,
        token,
        client_id,
        refresh_token,
    )

    # if we can lets go ahead and refresh
    if refresh_token and client_id:
        api._refresh_token()

    # e.g. if auth is correct the following command should print:
    # "{'message': 'Hello World, HMA'}"
    print(api.get())
