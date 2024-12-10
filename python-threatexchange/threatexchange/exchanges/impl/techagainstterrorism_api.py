# Copyright (c) Meta Platforms, Inc. and affiliates.

"""SignalExchangeAPI implementation for Tech Against Terrorism Hash List API"""


import typing as t
from dataclasses import dataclass

from threatexchange.exchanges.clients.techagainstterrorism import api
from threatexchange.exchanges import fetch_state as state
from threatexchange.exchanges import signal_exchange_api
from threatexchange.exchanges import auth
from threatexchange.exchanges.collab_config import CollaborationConfigWithDefaults
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
import logging


@dataclass
class TATCheckpoint(state.FetchCheckpointBase):
    checkpoint: str

    @classmethod
    def from_tat_fetch(cls, response: api.TATHashListResponse) -> "TATCheckpoint":
        logging.info(f"CHECKPOINT:{response.checkpoint}")
        return cls(response.checkpoint)


_TypedDelta = state.FetchDelta[
    t.Tuple[str, str],
    state.FetchedSignalMetadata,
    TATCheckpoint,
]


@dataclass
class TATCredentials(auth.CredentialHelper):
    ENV_VARIABLE: t.ClassVar[str] = "PYTX_TAT_CREDENTIALS"
    FILE_NAME: t.ClassVar[str] = "~/.pytx_tat_credentials"

    username: str
    password: str

    @classmethod
    def _from_str(cls, s: str) -> "TATCredentials":
        user, _, passw = s.strip().partition(":")
        return cls(user, passw)

    def _are_valid(self) -> bool:
        return bool(self.username and self.password)


class TATSignalExchangeAPI(
    auth.SignalExchangeWithAuth[CollaborationConfigWithDefaults, TATCredentials],
    signal_exchange_api.SignalExchangeAPIWithSimpleUpdates[
        CollaborationConfigWithDefaults,
        TATCheckpoint,
        state.FetchedSignalMetadata,
    ],
):

    def __init__(self, username, password) -> None:
        super().__init__()
        self.username = username
        self.password = password

    @staticmethod
    def get_config_cls() -> t.Type[CollaborationConfigWithDefaults]:
        return CollaborationConfigWithDefaults

    @staticmethod
    def get_checkpoint_cls() -> t.Type[TATCheckpoint]:
        return TATCheckpoint

    @staticmethod
    def get_record_cls() -> t.Type[state.FetchedSignalMetadata]:
        return state.FetchedSignalMetadata

    @staticmethod
    def get_credential_cls() -> t.Type[TATCredentials]:
        return TATCredentials

    @classmethod
    def get_name(cls) -> str:
        return "tat"

    @classmethod
    def for_collab(
        cls,
        collab: CollaborationConfigWithDefaults,
        credentials: t.Optional["TATCredentials"] = None,
    ) -> "TATSignalExchangeAPI":
        credentials = credentials or TATCredentials.get(cls)
        return cls(username=credentials.username, password=credentials.password)

    def get_client(self) -> api.TATHashListAPI:
        return api.TATHashListAPI(username=self.username, password=self.password)

    def fetch_iter(
        self,
        _supported_signal_types: t.Sequence[t.Type[SignalType]],
        checkpoint: t.Optional[TATCheckpoint],
    ) -> t.Iterator[_TypedDelta]:

        client = self.get_client()

        start_time = ""

        if checkpoint is not None:
            start_time = checkpoint.checkpoint

        for result in client.fetch_hashes_iter(start_time):

            if result.next is None:
                return

            translated = (_get_delta_mapping(r) for r in result.results)
            yield state.FetchDelta(
                dict(t for t in translated if t[0][0]),
                TATCheckpoint.from_tat_fetch(result),
            )


def _type_mapping() -> t.Dict[str, str]:
    return {
        "PDQ": PdqSignal.get_name(),
        "MD5": VideoMD5Signal.get_name(),
    }


def _get_delta_mapping(
    record: api.TATHashListEntry,
) -> t.Tuple[t.Tuple[str, str], t.Optional[state.FetchedSignalMetadata]]:

    type_str = _type_mapping().get(record.algorithm)
    metadata = state.FetchedSignalMetadata()

    return ((type_str, record.hash_digest), metadata)
