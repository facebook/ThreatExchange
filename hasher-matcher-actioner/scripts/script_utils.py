#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Utilities for hma script
"""

import json
import base64
import requests
import typing as t
from urllib.parse import urljoin


class HasherMatcherActionerAPI:
    def __init__(
        self,
        api_url: str,
        api_token: str,
    ) -> None:
        self.api_url = api_url
        self.api_token = api_token

    def _get_header(self) -> t.Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": self.api_token,
        }

    def _get_request_url(self, api_path: str) -> str:
        return urljoin(self.api_url, api_path)

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
        payload_bytes = json.dumps(payload).encode()

        response = requests.post(
            self._get_request_url(api_path),
            headers=self._get_header(),
            data=payload_bytes,
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

        payload_bytes = json.dumps(payload).encode()

        response = requests.post(
            self._get_request_url(api_path),
            headers=self._get_header(),
            data=payload_bytes,
        )

        response_json = response.json()
        put_response = requests.put(
            response_json["presigned_url"],
            data=file,
            headers={"content-type": "image/jpeg"},
        )


if __name__ == "__main__":
    # if you want hard code tests for additonal methods you can do so here
    pass
