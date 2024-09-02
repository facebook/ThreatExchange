# Copyright (c) Meta Platforms, Inc. and affiliates.

"""Simple implementation for the Tech Against Terrorism Hash List REST API"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import typing as t
from contextlib import contextmanager

import dacite
import requests
from requests.packages.urllib3.util.retry import Retry

# Maybe move to a common library someday
from threatexchange.exchanges.clients.fb_threatexchange.api import TimeoutHTTPAdapter


logger = logging.basicConfig(level=logging.INFO)


class TATIdeology(Enum):
  islamist = "islamist"
  far_right = "far-right"
  _all = "all"


@dataclass
class TATHashListResponse:
  file_url: t.AnyStr
  file_name: t.AnyStr
  created_on: datetime
  total_hashes: int
  ideology: TATIdeology


class TATEndpoint(Enum):
  authenticate = "token-auth/tcap/"
  hash_list = "api/hash-list"


class TATHashListAPI:
  """
  A wrapper around the Tech Against Terrorism Hash List API

  The verification and collection of terrorist content are conducted by TAT OSINT Analysts and automated processes. 
  Subsequently, the content is classified and hashed by the TAT Archive hashing and classification services.

  This API delivers a JSON file containing a comprehensive list of all hashed terrorist content within the TAT system.

  The list is refreshed nightly.
  """

  BASE_URL: t.ClassVar[t.AnyStr] = "https://beta.terrorismanalytics.org/"

  def __init__(
      self, 
      username: t.AnyStr,
      password: t.AnyStr
    ) -> None:
    self.username = username,
    self.password = password


  @contextmanager
  def _get_session(self, auth_token: t.Optional[t.AnyStr] = None):
    session = requests.Session()
    session.mount(
      self.BASE_URL,
      adapter=TimeoutHTTPAdapter(
        timeout=60,
        max_retries=Retry(
          total=4,
          status_forcelist=[429, 500, 502, 503, 504],
          # No retry for post. Could probably add timeout...
          allowed_methods=["HEAD", "GET", "OPTIONS"],
          backoff_factor=0.2,  # ~1.5 seconds of retries
        ),
      )
    )

    if auth_token:
      session.headers.update({"Authorization": f"Bearer {auth_token}"})

    try:
      yield session
    finally:
      session.close()


  def _get(self, endpoint: TATEndpoint, auth_token: t.Optional[t.AnyStr] = None) -> t.Any:
    """
        Perform an HTTP GET request, and return the JSON response payload.

        Same timeouts and retry strategy as `_get_session` above.
    """
    with self._get_session(auth_token) as session:
      url = self.BASE_URL + endpoint
      response = session.get(url=url)
      response.raise_for_status()
      return response.json()


  def _post(self, endpoint: TATEndpoint, data=None) -> t.Any:
    """
        Perform an HTTP POST request, and return the JSON response payload.

        Same timeouts and retry strategy as `_get_session` above.
    """
    with self._get_session() as session:
      url = self.BASE_URL + endpoint
      response = session.post(url=url, data=data)
      response.raise_for_status()
      return response.json()


  def authenticate(self, username: t.AnyStr, password: t.AnyStr) -> t.AnyStr | None:
    """
    Authenticate with TCAP services and obtain a JWT token
    """
    logger.info("Authenticating with TCAP: %s", username)

    try:
      auth_response = self._post(
        TATEndpoint.authenticate, 
        data={"username": username, "password": password}
      )
      return auth_response.get("token")
    
    except Exception as e:
      logger.error("Error authenticating with TCAP: %s", e)
      return None



  def get_hash_list(self, ideology: TATIdeology = TATIdeology._all) -> TATHashListResponse | None:
    """
    Get the Hash List presigned URL ( 5 Minute expiry ) and metadata: TATHashListResponse
    """

    try:
      token = self.authenticate(self.username, self.password)

      if token is not None:
        logger.info("Getting hash list")
        response = self._get(
          TATEndpoint.hash_list + ideology.value,
          auth_token=token
        )

        return response
      
      else:
        logger.error("Error getting hash list: %s", e)
        raise Exception("Unable authenticating with TCAP")
      
    except Exception as e:
      logger.error("Error getting hash list: %s", e)
      return None
    


