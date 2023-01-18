# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Common operations that you would use when implementing a client for an external
API. This is not necessarily a Graph API, but any other HTTP Based API that HMA
needs to support.
"""

# TODO Remove same methods in python-threatexchange api.py

import typing as t
import urllib.parse

import requests
from requests.adapters import HTTPAdapter
from requests.sessions import Session
from urllib3.util.retry import Retry


class TimeoutHTTPAdapter(HTTPAdapter):
    """
    Plug into requests to get a well-behaved session that does not wait for eternity.
    H/T: https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/#setting-default-timeouts
    """

    def __init__(self, *args, timeout=5, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, *, timeout=None, **kwargs):
        if timeout is None:
            timeout = self.timeout
        return super().send(request, timeout=timeout, **kwargs)


class BaseAPI:
    _base_url: str

    def get_json_from_url(
        self, url, params=None, *, json_obj_hook: t.Callable = None, headers=None
    ):
        """
        Perform an HTTP GET request, and return the JSON response payload.
        Same timeouts and retry strategy as `_get_session` above.
        """
        with self._get_session() as session:
            response = requests.get(url, params=params or {}, headers=headers or {})
            response.raise_for_status()
            return response.json(object_hook=json_obj_hook)

    def _get_session(self) -> Session:
        """
        Custom requests sesson

        Ideally, should be used within a context manager:
        ```
        with self._get_session() as session:
            session.get()...
        ```

        If using without a context manager, ensure you end up calling close() on
        the returned value.
        """
        session = requests.Session()
        session.mount(
            self._base_url,
            adapter=TimeoutHTTPAdapter(
                timeout=60,
                max_retries=Retry(
                    total=4,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["HEAD", "GET", "OPTIONS"],
                    backoff_factor=0.2,  # ~1.5 seconds of retries
                ),
            ),
        )
        return session

    def _get_api_url(self, sub_path: t.Optional[str], query_dict: t.Dict = {}) -> str:
        """
        Returns a URL for a sub-path and a dictionary of query
        parameters.
        """

        query = urllib.parse.urlencode(query_dict)

        base_url_parts = urllib.parse.urlparse(self._base_url)
        url_parts = urllib.parse.ParseResult(
            base_url_parts.scheme,
            base_url_parts.netloc,
            f"{base_url_parts.path}/{sub_path}",
            base_url_parts.params,
            query,
            base_url_parts.fragment,
        )

        return urllib.parse.urlunparse(url_parts)
