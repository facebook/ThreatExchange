# Copyright (c) Meta Platforms, Inc. and affiliates.

"""Simple implementation for the Tech Against Terrorism Hash List REST API"""

from dataclasses import dataclass
from datetime import datetime
import enum
import requests
import logging
import typing as t
from contextlib import contextmanager
import requests
from requests.packages.urllib3.util.retry import Retry
from threatexchange.exchanges.clients.utils.common import TimeoutHTTPAdapter


class TATIdeology(enum.Enum):
    islamist = "islamist"
    far_right = "far-right"
    _all = "all"


@dataclass
class TATAPIErrorResponse:
    error: str


@dataclass
class TATHashListResponse:
    file_url: str
    file_name: str
    created_on: datetime
    total_hashes: int
    ideology: str


@dataclass
class TATHashRecord:
    id: int
    hash_digest: str
    algorithim: str
    ideology: str
    file_type: str


@enum.unique
class TATSignalType(enum.Enum):
    """What the serialized hash represents"""

    Unknown = "Unknown"
    PDQ = "ImagePDQ"
    MD5 = "VideoMD5"


@dataclass
class TATUser:
    user: t.Dict[str, t.Any]
    token: str


class TATEndpoint(enum.Enum):
    authenticate = "token-auth/tcap/"
    hash_list = "api/hash-list"


class TATHashListAPI:
    """
    A wrapper around the Tech Against Terrorism Hash List API

    The verification and collection of terrorist content are conducted by TAT OSINT Analysts and automated processes.
    Subsequently, the content is classified and hashed by the TAT Archive hashing and classification services.

    This API delivers a JSON file containing a comprehensive list of all hashed terrorist content within the TAT system.

    The list is refreshed daily.

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
        full_url: t.Optional[str] = None,
    ) -> t.Any:
        """
        Perform an HTTP GET request, and return the JSON response payload.

        Same timeouts and retry strategy as `_get_session` above.
        """

        with self._get_session(auth_token) as session:
            url = full_url if full_url else self.BASE_URL + (endpoint or "")
            response = session.get(url=url)
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

        if not isinstance(username, str) or not isinstance(password, str):
            logging.error("Username or password not valid")
            raise ValueError("Username or password not valid")

        logging.info("Authenticating with TCAP: %s", username)

        auth_response = self._post(
            TATEndpoint.authenticate,
            data={"username": username, "password": password, "resend": False},
        )
        return auth_response.get("token")

    def get_hash_list(
        self, ideology: str = TATIdeology._all.value
    ) -> t.List[t.Dict[str, str]]:
        """
        Get the Hash List JSON file presigned URL ( 5 Minute expiry ) and metadata
        """

        try:
            token = self.get_auth_token(self.username, self.password)
            endpoint = f"{TATEndpoint.hash_list.value}/{ideology}"

            logging.info("Fetching TAT hash list")

            # Get the hash list request response
            response = self._get(endpoint, auth_token=token)

            # Use the pre-signed url from the response to download the hash list values
            hash_list = self._get(full_url=response["file_url"])

            return hash_list

        except Exception as exception:
            logging.error("Failed to get hash list: %s", exception)
            raise
