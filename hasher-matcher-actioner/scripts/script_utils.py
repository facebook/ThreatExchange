#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Utilities for hma script
"""

import json
import base64
import requests
import typing as t


def send_single_submission_url(
    url: str,
    content_id: str,
    file: t.BinaryIO,
    token: str,
    additional_fields: t.List[str],
):

    payload = {
        "submission_type": "POST_URL_UPLOAD",
        "content_id": content_id,
        "content_type": "PHOTO",
        "content_bytes_url_or_file_type": "image/jpeg",
        "additional_fields": [],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": token,
    }

    payload_bytes = json.dumps(payload).encode()

    response = requests.post(url, headers=headers, data=payload_bytes)
    response_json = response.json()
    put_response = requests.put(
        response_json["presigned_url"],
        data=file,
        headers={"content-type": "image/jpeg"},
    )


def send_single_submission_b64(
    url: str,
    content_id: str,
    file: t.BinaryIO,
    token: str,
    additional_fields: t.List[str] = [],
):

    payload = {
        "submission_type": "DIRECT_UPLOAD",
        "content_id": content_id,
        "content_type": "PHOTO",
        "content_bytes_url_or_file_type": str(base64.b64encode(file.read()), "utf-8"),
        "additional_fields": additional_fields,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": token,
    }

    payload_bytes = json.dumps(payload).encode()

    response = requests.post(url, headers=headers, data=payload_bytes)
