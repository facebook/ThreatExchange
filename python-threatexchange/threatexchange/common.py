#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
A place to put simple helpers that don't seem like they go anywhere else.

If this file starts getting large, break it up.
"""

import re
from requests.adapters import HTTPAdapter


def class_name_to_human_name(name: str, suffix: str) -> str:
    """Helper to make human-friendly names using a class name as a template"""
    if name.endswith(suffix):
        name = name[: -len(suffix)]
    return camel_case_to_underscore(name)


def camel_case_to_underscore(name: str) -> str:
    """
    Convert name in camel-case notation into lowercase+underscore notation.

    For example, AbcXyz will be converted into abc_xyz.
    TODO: Maybe should live in some kind of common location
    """
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


DEFAULT_TIMEOUT = 5  # seconds


class TimeoutHTTPAdapter(HTTPAdapter):
    """Plug into requests to get a well-behaved session that does not wait for eternity.
    H/T: https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/#setting-default-timeouts
    """

    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)
