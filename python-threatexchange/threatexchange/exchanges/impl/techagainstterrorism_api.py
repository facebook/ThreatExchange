# Copyright (c) Meta Platforms, Inc. and affiliates.

"""SignalExchangeAPI implementation for Tech Against Terrorism Hash List API"""


from functools import lru_cache
import json
import tempfile
import requests
import time
import typing as t
from dataclasses import dataclass, field

from threatexchange.exchanges.clients.techagainstterrorism import api

from threatexchange.exchanges import fetch_state as state
from threatexchange.exchanges import signal_exchange_api
from threatexchange.exchanges import auth
from threatexchange.exchanges.collab_config import (
    CollaborationConfigBase,
    CollaborationConfigWithDefaults,
)
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.url import URLSignal
from threatexchange.signal_type.raw_text import RawTextSignal


@dataclass
class TATCheckpoint(state.FetchCheckpointBase):
    """
    Tech Against Terrorism Hash List revolves around fetching
    a JSON file which contains a list of hashes. The pre-signed URL
    for the JSON file is returned from the API response.

    The Hash List is updated nightly and new hashes are appended to the list.

    For more information on our collection process please visit: 
    - https://terrorismanalytics.org/about/how-it-works

    For our Hash List documentation: 
    - https://terrorismanalytics.org/docs/hash-list-v1
    """

    last_fetch_time: int

    def is_stale(self) -> bool:
        """
        Given out hash list API does not support incremental fetching, 
        the fetch will always be stale.
        """
        return time.time() - self.last_fetch_time > 3600 * 24

    @classmethod
    def from_tat_fetch(cls, response: api.TATHashListResponse) -> "TATCheckpoint":
        return cls(int(response.created_on.timestamp()))


@dataclass
class TATSignalMetadata(state.FetchedSignalMetadata):
    """ 
    Our current Hash List API does not support tags and is a broadcast API only.
    """

    pass


@dataclass
class TATCredentials(auth.CredentialHelper):
    ENV_VARIABLE: t.ClassVar[str] = "TX_TAT_CREDENTIALS"
    FILE_NAME: t.ClassVar[str] = "~/.tx_tat_credentials"

    username: str
    password: str

    @classmethod
    def _from_str(cls, s: str) -> "TATCredentials":
        user, _, passw = s.strip().partition(":")
        return cls(user, passw)

    def _are_valid(self) -> bool:
        return bool(self.username and self.password)


class TATSignalExchangeAPI(
    auth.SignalExchangeWithAuth[CollaborationConfigBase, TATCredentials],
    signal_exchange_api.SignalExchangeAPIWithSimpleUpdates[
        CollaborationConfigBase, TATCheckpoint, TATSignalMetadata
    ],
):

    def __init__(self, username, password) -> None:
        super().__init__()
        self.username = username
        self.password = password

    @staticmethod
    def get_config_cls() -> t.Type[CollaborationConfigBase]:
        return CollaborationConfigBase

    @staticmethod
    def get_checkpoint_cls() -> t.Type[TATCheckpoint]:
        return TATCheckpoint

    @staticmethod
    def get_record_cls() -> type[TATSignalMetadata]:
        return TATSignalMetadata

    @classmethod
    def for_collab(
        cls,
        collab: CollaborationConfigBase,
        credentials: t.Optional[TATCredentials] = None,
    ) -> "TATSignalExchangeAPI":
        credentials = credentials or TATCredentials.get(cls)
        return cls(
            collab,
            api.TATHashListAPI(
                username=credentials.username, password=credentials.password
            ),
        )

    def get_client(self) -> api.TATHashListAPI:
        return api.TATHashListAPI(username=self.username, password=self.password)

    def fetch_iter(
        self,
        _supported_signal_types: t.Sequence[t.Type[SignalType]],
        checkpoint: t.Optional[TATCheckpoint],
    ) -> t.Iterator[
        state.FetchDelta[t.Tuple[str, str], TATSignalMetadata, TATCheckpoint]
    ]:
        """
         The TAT Hash List returns a JSON file containing all hashes in our system.
        """

        client = self.get_client()
        result = client.get_hash_list()

        # Download the JSON file from the presigned URL
        response = requests.get(result.file_url)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=True) as f:
            f.write(response.content)
            f.close()

            # Read the JSON file and load into memory
            with open(f.name, "r") as file:
                data = json.load(file)

                translated = (_get_delta_mapping(entry) for entry in data)
                yield state.FetchDelta(
                    dict(t for t in translated if t[0][0]),
                    checkpoint=TATCheckpoint.from_tat_fetch(result),
                )


def _get_delta_mapping(
    record: api.TATHashRecord,
) -> t.Tuple[t.Tuple[str, str], t.Optional[TATSignalMetadata]]:

    metadata = None  # Unsure at this time
    return ((str(record.id), record.hash_digest), metadata)
