# Copyright (c) Meta Platforms, Inc. and affiliates.

"""Simple implementation for the Tech Against Terrorism Hash List REST API"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import requests
import logging
import typing as t
from contextlib import contextmanager
import requests
from requests.packages.urllib3.util.retry import Retry
from threatexchange.exchanges.clients.utils.common import TimeoutHTTPAdapter


class TATIdeology(Enum):
    islamist = "islamist"
    far_right = "far-right"
    _all = "all"


@dataclass
class TATAPIErrorResponse:
    error: str


@dataclass
class TATHashListEntry:
    hash_digest: str
    algorithm: str
    ideology: TATIdeology
    file_type: str
    deleted: bool
    updated_on: float
    id: int


@dataclass
class TATHashListResponse:
    count: int
    next: t.Optional[str]
    previous: t.Optional[str]
    checkpoint: str
    results: t.List[TATHashListEntry]


@dataclass
class TATUser:
    user: t.Dict[str, t.Any]
    token: str


class TATEndpoint(Enum):
    authenticate = "token-auth/tcap/"
    hash_list = "api/hash-list/v2/all"


class TATHashListAPI:
    """
    A wrapper around the Tech Against Terrorism Hash List API

    The verification and collection of terrorist content are conducted by TAT OSINT Analysts and automated processes.
    Subsequently, the content is classified and hashed by the TAT Archive hashing and classification services.

    The list is udpated in real-time as content is classified or captured.

    For more information on our collection process please visit: https://terrorismanalytics.org/about/how-it-works
    For our Hash List documentation: https://terrorismanalytics.org/docs/hash-list-v1
    """

    BASE_URL: t.ClassVar[str] = "https://beta.terrorismanalytics.org/"

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    @contextmanager
    def _get_session(self, auth_token: t.Optional[str] = None):
        session = requests.Session()
        session.mount(
            self.BASE_URL,
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

        if auth_token:
            session.headers.update({"Authorization": f"Bearer {auth_token}"})

        try:
            yield session
        finally:
            session.close()

    def _get(
        self,
        endpoint: t.Optional[str] = None,
        auth_token: t.Optional[str] = None,
        **params,
    ) -> t.Any:
        """
        Perform an HTTP GET request, and return the JSON response payload.

        Same timeouts and retry strategy as `_get_session` above.
        """
        full_url = self.BASE_URL + (endpoint or "")

        with self._get_session(auth_token) as session:
            response = session.get(url=full_url, params=params)
            response.raise_for_status()
            return response.json()

    def _post(self, endpoint: TATEndpoint, data=None) -> t.Any:
        """
        Perform an HTTP POST request, and return the JSON response payload.

        Same timeouts and retry strategy as `_get_session` above.
        """
        with self._get_session() as session:
            url = self.BASE_URL + endpoint.value
            response = session.post(url=url, data=data)
            response.raise_for_status()
            return response.json()

    def get_auth_token(self, username: str, password: str) -> t.Optional[str]:
        """
        Authenticate with TCAP services and obtain a JWT token
        """

        logging.info("Authenticating with TCAP: %s", username)

        auth_response = self._post(
            TATEndpoint.authenticate,
            data={"username": username, "password": password, "resend": False},
        )
        return auth_response.get("token")

    def fetch_hashes(
        self,
        order: str = "asc",
        after: str = "",
    ) -> TATHashListResponse:
        """
        Get the Hash List JSON file presigned URL ( 5 Minute expiry ) and metadata
        """

        params: t.Dict[str, t.Any] = {
            "order": order,
            "after": after,
        }

        try:
            token = self.get_auth_token(self.username, self.password)
            endpoint = f"{TATEndpoint.hash_list.value}"

            logging.info("Fetching TAT hash list")

            results = self._get(endpoint, auth_token=token, **params)

            return results

        except Exception as exception:
            logging.error("Failed to get hash list: %s", exception)
            raise

    def fetch_hashes_iter(self, next_page: str) -> t.Iterator[TATHashListResponse]:
        """
        A wrapper to continously fetch the hash list in a paginated manner.
        Each page has 3 elements we're interested in here:

        - next (str | None): A URL with limit and offset query params automatically applied if there are more results.
        - checkpoint (str): A timestamp and id of the last record in the current page eg: 1704085200,124
        - results (List[TATHashListEntry]): A list of hash list entries

        if next in null we have no more hashes left to fetch meaning we break out of the loop
        """

        has_more = True
        next_page = next_page

        while has_more:
            response = self.fetch_hashes(after=next_page)
            next_page = response["checkpoint"]
            has_more = bool(response["next"])

            yield response
