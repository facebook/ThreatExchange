# Copyright (c) Meta Platforms, Inc. and affiliates.

"""Simple implementation for the Tech Against Terrorism Hash List REST API"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import typing as t
from contextlib import contextmanager
import requests
from requests.packages.urllib3.util.retry import Retry

# Maybe move to a common library someday
from threatexchange.exchanges.clients.fb_threatexchange.api import TimeoutHTTPAdapter


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

@dataclass
class TATUser:
  user: t.Any
  token: t.AnyStr

class TATEndpoint(Enum):
  authenticate = "token-auth/tcap/"
  hash_list = "api/hash-list"


class TATHashListAPI:
  """
  A wrapper around the Tech Against Terrorism Hash List API

  The verification and collection of terrorist content are conducted by TAT OSINT Analysts and automated processes. 
  Subsequently, the content is classified and hashed by the TAT Archive hashing and classification services.

  This API delivers a JSON file containing a comprehensive list of all hashed terrorist content within the TAT system.

  The list is refreshed daily.
  """

  BASE_URL: t.ClassVar[t.AnyStr] = "https://beta.terrorismanalytics.org/"

  def __init__(
      self, 
      username: t.AnyStr,
      password: t.AnyStr
    ) -> None:
    self.username = username
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

    if not isinstance(username, str) or not isinstance(password, str):
      logging.error("Username or password not valid")
      return None

    logging.info("Authenticating with TCAP: %s", username)


    try:
      auth_response = self._post(
        TATEndpoint.authenticate.value, 
        data={"username": username, "password": password, "resend": False}
      )
      return auth_response.get("token")
    
    except Exception as e:
      logging.error("Error authenticating with TCAP: %s", e)
      return None



  def get_hash_list(self, ideology: TATIdeology = TATIdeology._all.value) -> TATHashListResponse | None:
    """
    Get the Hash List JSON file presigned URL ( 5 Minute expiry ) and metadata: TATHashListResponse
    """

    try:
      token = self.authenticate(self.username, self.password)

      if token is not None:
        logging.info("Fetching hash list")
        response = self._get(
          f"{TATEndpoint.hash_list.value}/{ideology}",
          auth_token=token
        )
        
        return response
    
      else:
        logging.error("Error getting hash list: %s", e)
        raise Exception("Unable authenticating with TCAP")

    except requests.exceptions.HTTPError as http_err:
        return {"http_error": str(http_err)}
      
      
    except Exception as e:
      logging.error("Error getting hash list: %s", e)
      return {"error": str(e)}
    


