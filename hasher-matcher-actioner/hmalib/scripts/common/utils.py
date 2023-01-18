#! /usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

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
        transport_adapter: HTTPAdapter = None,
    ) -> None:
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "content-type": "application/json",
                "Authorization": api_token,
            }
        )
        if transport_adapter:
            self.add_transport_adapter(transport_adapter)

    def add_transport_adapter(self, transport_adapter: HTTPAdapter):
        self.session.mount(self.api_url, transport_adapter)

    def _get_request_url(self, api_path: str) -> str:
        return urljoin(self.api_url, api_path)

    def get(self, api_path: str = "root/"):
        response = self.session.get(self._get_request_url(api_path))
        return response.json()

    def get_all_matches(self, api_path: str = "matches/"):
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
        api_path: str = "submit/bytes/"
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
        api_path: str = "submit/put-url/"
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
        content_id: str,
        url: str,
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
        api_path: str = "submit/url/"
        response = self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )
        response.raise_for_status()

    def submit_via_s3_object(
        self,
        content_id: str,
        bucket_name: str,
        object_key: str,
        content_type: str = "photo",
        additional_fields: t.List[str] = [],
    ):
        """
        Submit to the API using a s3 object that api_root is authorized to read from
        """
        payload = {
            "content_id": content_id,
            "content_type": content_type,
            "additional_fields": additional_fields,
            "bucket_name": bucket_name,
            "object_key": object_key,
        }
        api_path: str = "submit/s3/"
        response = self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )
        response.raise_for_status()

    def submit_via_hash(
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
        api_path: str = "submit/hash/"
        response = self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )
        response.raise_for_status()

    @classmethod
    def sns_submit_via_external_url(
        cls,
        submit_topic_arn: str,
        content_id: str,
        url: str,
        additional_fields: t.List[str] = [],
    ):
        """
        Distinct from submit_via_upload_put_url(), It uses the URL only path
        and bypasses s3 completely and submits via an SNS topic
        """
        payload = {
            "content_id": content_id,
            "content_type": "photo",
            "additional_fields": additional_fields,
            "content_url": url,
        }
        sns_client = boto3.client("sns")

        response = sns_client.publish(
            TopicArn=submit_topic_arn,
            Message=json.dumps(payload),
        )

    @classmethod
    def sns_submit_via_s3_object(
        cls,
        submit_topic_arn: str,
        content_id: str,
        bucket_name: str,
        object_key: str,
        content_type: str = "photo",
        additional_fields: t.List[str] = [],
    ):
        """
        Submit to the SNS topic using a s3 object that submit_even_handler lambda is authorized to read from.
        """
        payload = {
            "content_id": content_id,
            "content_type": content_type,
            "additional_fields": additional_fields,
            "bucket_name": bucket_name,
            "object_key": object_key,
        }
        sns_client = boto3.client("sns")

        response = sns_client.publish(
            TopicArn=submit_topic_arn,
            Message=json.dumps(payload),
        )

    def get_content_hash_details(
        self,
        content_id: str,
        api_path: str = "content/hash/",
    ):
        return self.session.get(
            self._get_request_url(api_path),
            params={"content_id": content_id},
        ).json()

    def get_content_action_history(
        self,
        content_id: str,
        api_path: str = "content/action-history/",
    ):
        response = self.session.get(
            self._get_request_url(api_path),
            params={"content_id": content_id},
        )
        return response.json().get("action_history", [])

    def get_content_matches(
        self,
        content_id: str,
        api_path: str = "matches/match/",
    ):
        response = self.session.get(
            self._get_request_url(api_path),
            params={"content_id": content_id},
        )
        return response.json().get("match_details", [])

    def get_dataset_configs(
        self,
        api_path: str = "datasets/",
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
        api_path: str = "datasets/create",
    ):
        payload = {
            "privacy_group_id": privacy_group_id,
            "privacy_group_name": privacy_group_name,
            "description": description,
            "fetcher_active": fetcher_active,
            "matcher_active": matcher_active,
            "write_back": write_back,
        }
        return self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )

    def get_actions(
        self,
        api_path: str = "actions/",
    ):
        response = self.session.get(self._get_request_url(api_path))
        return response.json().get("actions_response", [])

    def create_action(
        self,
        name: str,
        config_subtype: str,
        fields: t.Dict[str, t.Any],
        api_path: str = "actions/",
    ):
        payload = {
            "name": name,
            "config_subtype": config_subtype,
            "fields": fields,
        }
        return self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )

    def delete_action(
        self,
        action_name: str,
        api_path: str = "actions/",
    ):
        return self.session.delete(self._get_request_url(api_path + action_name))

    def get_action_rules(
        self,
        api_path: str = "action-rules/",
    ):
        response = self.session.get(self._get_request_url(api_path))
        return response.json().get("action_rules", [])

    def create_action_rule(
        self,
        action_rule: t.Any,
        api_path: str = "action-rules/",
    ):
        payload = {
            "action_rule": action_rule,
        }
        return self.session.post(
            self._get_request_url(api_path),
            data=json.dumps(payload).encode(),
        )

    def delete_action_rule(
        self,
        action_rule_name: str,
        api_path: str = "action-rules/",
    ):
        return self.session.delete(self._get_request_url(api_path + action_rule_name))

    def get_matches_for_hash(
        self,
        signal_type: str,
        signal_value: str,
        api_path: str = "matches/for-hash/",
    ):
        params = {
            "signal_type": signal_type,
            "signal_value": signal_value,
        }
        response = self.session.get(
            self._get_request_url(api_path),
            params=params,
        )
        return response.json().get("matches", [])


def get_terraform_outputs(
    directory: str = "terraform",
) -> t.Dict[str, str]:
    """
    Converts from the super verbose JSON output to a more natural string -> string map.
    """
    cmd = ["terraform"]
    cmd.extend(["output", "-json"])
    out = json.loads(subprocess.check_output(cmd, cwd=directory))
    return {k: out[k]["value"] for k in out}


def get_cached_terraform_outputs(
    path: str = "tmp.out",
) -> t.Dict[str, str]:
    """
    Gets output if not already present at path.
    """
    file_exists = os.path.exists(path)

    if not file_exists:
        with open(path, "w") as f:
            outputs = get_terraform_outputs()
            f.write(json.dumps(outputs))
            return outputs

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
    token_default: str = TOKEN,
    prompt_for_token: bool = False,
):

    token = os.environ.get(
        "HMA_TOKEN",
        token_default,
    )

    if not token:
        if prompt_for_token:
            print("Need an access token to authenticate.")
            token = input("Enter token: ")
        else:
            print("Authentication requires HMA_TOKEN be present in ENV.")
            exit()

    return token


if __name__ == "__main__":
    # If you want hard code tests for methods you can do so here:

    # Testing HasherMatcherActionerAPI
    #   Since the API requries a deployed instance the majority of
    #   testing needs to be done manually. See below.
    print("Manual Test of API Request Methods:")

    tf_outputs = get_terraform_outputs()

    api_url = tf_outputs["api_url"]
    token = get_auth_from_env()

    api = HasherMatcherActionerAPI(
        api_url,
        token,
    )
    # e.g. if auth is correct the following command should print:
    # "{'message': 'Hello World, HMA'}"
    print(api.get())
