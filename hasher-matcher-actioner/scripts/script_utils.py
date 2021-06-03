#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Utilities for hma scripts
"""

import json
import base64
import requests
import typing as t
from urllib.parse import urljoin


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
    ) -> None:
        self.api_url = api_url
        self.api_token = api_token
        self.client_id = client_id
        self.refresh_token = refresh_token

    def _refresh_token(self):
        """
        IdToken has a default ttl of 60 minutes
        RefreshToken as a default ttl of 30 days
        Only works in boto3 is install and optional values are set.
        """
        if self.client_id and self.refresh_token:
            import boto3

            client = boto3.client("cognito-idp")

            resp = client.initiate_auth(
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={"REFRESH_TOKEN": self.refresh_token},
                ClientId=self.client_id,
            )
            self.api_token = resp["AuthenticationResult"]["IdToken"]
            return self.api_token
        return "Refresh Token and/or client ID Missing"

    def _get_header(self) -> t.Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": self.api_token,
        }

    def _get_request_url(self, api_path: str) -> str:
        return urljoin(self.api_url, api_path)

    def _get_with_auth(
        self,
        api_path: str = "",
        params: t.Optional[t.Dict[str, str]] = None,
    ) -> requests.Response:
        return requests.get(
            self._get_request_url(api_path),
            headers=self._get_header(),
        )

    def _post_with_auth(
        self,
        api_path: str = "",
        data: t.Optional[bytes] = None,
    ) -> requests.Response:
        return requests.post(
            self._get_request_url(api_path),
            headers=self._get_header(),
            data=data,
        )

    def get_all_matches(self, api_path: str = "/matches/"):
        response = self._get_with_auth(api_path=api_path)
        return response.json().get("match_summaries", [])

    def send_single_submission_b64(
        self,
        content_id: str,
        file: t.BinaryIO,
        additional_fields: t.List[str] = [],
        api_path: str = "/submit/",
    ):
        payload = {
            "submission_type": "DIRECT_UPLOAD",
            "content_id": content_id,
            "content_type": "PHOTO",
            "content_bytes_url_or_file_type": str(
                base64.b64encode(file.read()), "utf-8"
            ),
            "additional_fields": additional_fields,
        }
        self._post_with_auth(
            api_path=api_path,
            data=json.dumps(payload).encode(),
        )

    def send_single_submission_url(
        self,
        content_id: str,
        file: t.BinaryIO,
        additional_fields: t.List[str],
        api_path: str = "/submit/",
    ):
        payload = {
            "submission_type": "POST_URL_UPLOAD",
            "content_id": content_id,
            "content_type": "PHOTO",
            "content_bytes_url_or_file_type": "image/jpeg",
            "additional_fields": [],
        }
        response = self._post_with_auth(
            api_path=api_path,
            data=json.dumps(payload).encode(),
        )

        response_json = response.json()
        put_response = requests.put(
            response_json["presigned_url"],
            data=file,
            headers={"content-type": "image/jpeg"},
        )

    def get_content_hash_details(
        self,
        content_id: str,
        api_path: str = "/content/hash/",
    ):
        response = self._get_with_auth(
            api_path=api_path,
            params={"content_id": content_id},
        )
        return response.json()

    def get_content_action_history(
        self,
        content_id: str,
        api_path: str = "/content/action-history/",
    ):
        response = self._get_with_auth(
            api_path=api_path,
            params={"content_id": content_id},
        )
        return response.json().get("action_history", [])

    def get_content_matches(
        self,
        content_id: str,
        api_path: str = "/matches/match/",
    ):
        response = self._get_with_auth(
            api_path=api_path,
            params={"content_id": content_id},
        )
        return response.json().get("match_details", [])

    def get_dataset_configs(
        self,
        api_path: str = "/datasets/",
    ):
        response = self._get_with_auth(api_path=api_path)
        return response.json().get("threat_exchange_datasets", [])

    def create_dataset_config(
        self,
        privacy_group_id: str,
        privacy_group_name: str,
        description: str = "",
        matcher_active: bool = True,
        fetcher_active: bool = False,
        write_back: bool = False,
        api_path: str = "/datasets/create/",
    ):
        payload = {
            "privacy_group_id": privacy_group_id,
            "privacy_group_name": privacy_group_name,
            "description": description,
            "fetcher_active": fetcher_active,
            "matcher_active": matcher_active,
            "write_back": write_back,
        }
        self._post_with_auth(
            api_path=api_path,
            data=json.dumps(payload).encode(),
        )

    def get_actions(
        self,
        api_path: str = "/actions/",
    ):
        response = self._get_with_auth(api_path=api_path)
        return response.json().get("actions_response", [])

    def create_action(
        self,
        action_name: str,
        config_subtype: str,
        fields: t.Dict[str, t.Any],
        api_path: str = "/actions/",
    ):
        payload = {
            "action_name": action_name,
            "config_subtype": config_subtype,
            "fields": fields,
        }
        self._post_with_auth(
            api_path=api_path,
            data=json.dumps(payload).encode(),
        )

    def get_action_rules(
        self,
        api_path: str = "/action-rules/",
    ):
        response = self._get_with_auth(api_path=api_path)
        return response.json().get("action_rules", [])

    def create_action_rule(
        self,
        action_rule: t.Any,
        api_path: str = "/action-rules/",
    ):
        payload = {
            "action_rule": action_rule,
        }
        self._post_with_auth(
            api_path=api_path,
            data=json.dumps(payload).encode(),
        )


if __name__ == "__main__":
    # If you want hard code tests for methods you can do so here:

    # Testing HasherMatcherActionerAPI
    #   Since the API requries a deployed instance the majority of
    #   testing needs to be done manually. See below.

    # Add init values for the api:

    TOKEN = ""
    # i.e. "https://<app-id>.execute-api.<region>.amazonaws.com/"
    API_URL = ""
    # See AWS Console: Cognito -> UserPools... -> App clients
    CLIENT_ID = ""
    # Can be created with dev certs `$ scripts/get_auth_token --refresh_token`
    REFRESH_TOKEN = ""

    api = HasherMatcherActionerAPI(API_URL, TOKEN, CLIENT_ID, REFRESH_TOKEN)

    print("Manual Test of API Request Methods:")

    # Space to test api
    # e.g. if auth is correct the following command should print:
    # "{'message': 'Hello World, HMA <#>'}"

    print(api._get_with_auth().json())
