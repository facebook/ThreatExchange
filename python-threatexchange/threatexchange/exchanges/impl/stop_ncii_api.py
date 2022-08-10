# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""SignalExchangeAPI implementation for StopNCII.org"""


from functools import lru_cache
import time
import typing as t
from dataclasses import dataclass

from threatexchange.exchanges.clients.stopncii import api

from threatexchange.exchanges import fetch_state as state
from threatexchange.exchanges import signal_exchange_api
from threatexchange.exchanges import auth
from threatexchange.exchanges.collab_config import (
    CollaborationConfigBase,
)
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.url import URLSignal
from threatexchange.signal_type.raw_text import RawTextSignal


@dataclass
class StopNCIICheckpoint(
    state.FetchCheckpointBase,
):
    update_time: int
    last_fetch_time: int

    def is_stale(self) -> bool:
        """Consider stale after 30d of not fetching"""
        return time.time() - self.last_fetch_time > 3600 * 24 * 30

    def get_progress_timestamp(self) -> t.Optional[int]:
        return self.update_time

    @classmethod
    def from_stopncii_fetch(
        cls, response: api.FetchHashesResponse
    ) -> "StopNCIICheckpoint":
        return cls(response.nextSetTimestamp, int(time.time()))


@dataclass
class StopNCIISignalMetadata(state.FetchedSignalMetadata):
    feedbacks: t.List[api.StopNCIICSPFeedback]

    def get_as_opinions(self) -> t.Sequence[state.SignalOpinion]:
        # TODO - handle which opinions are mine
        opinions = [
            state.SignalOpinion(False, _opinion_mapping(f.feedbackValue), f.tags)
            for f in self.feedbacks
        ]
        # implicitly, all records from StopNCII are from user-submitted cases
        opinions.append(
            state.SignalOpinion(
                False, state.SignalOpinionCategory.INVESTIGATION_SEED, set()
            ),
        )
        return opinions


@dataclass
class StopNCIICredentials(auth.CredentialHelper):
    ENV_VARIABLE: t.ClassVar[str] = "TX_STOPNCII_KEYS"
    FILE_NAME: t.ClassVar[str] = "~/.tx_stopncii_keys"

    function_key: str
    subscription_key: str

    @classmethod
    def _from_str(cls, s: str) -> "StopNCIICredentials":
        user, _, passw = s.strip().partition(",")
        return cls(user, passw)

    def _are_valid(self) -> bool:
        return bool(self.function_key and self.subscription_key)


class StopNCIISignalExchangeAPI(
    auth.SignalExchangeWithAuth[CollaborationConfigBase, StopNCIICredentials],
    signal_exchange_api.SignalExchangeAPIWithSimpleUpdates[
        CollaborationConfigBase,
        StopNCIICheckpoint,
        StopNCIISignalMetadata,
    ],
):
    """
    Conversion for the StopNCII.org API

    Key implementation details:
        1. Changes the key to be the SignalType names during fetch,
        2. Owner names are stored exposed as strings - no ids
        3. Both feedback and hash upload on API, but only feedback is available
           on server as of 4/14
    """

    def __init__(
        self,
        collab: CollaborationConfigBase,
        client: api.StopNCIIAPI,
    ) -> None:
        super().__init__()
        self.collab = collab
        self.api = client

    @staticmethod
    def get_config_cls() -> t.Type[CollaborationConfigBase]:
        return CollaborationConfigBase

    @staticmethod
    def get_checkpoint_cls() -> t.Type[StopNCIICheckpoint]:
        return StopNCIICheckpoint

    @staticmethod
    def get_record_cls() -> t.Type[StopNCIISignalMetadata]:
        return StopNCIISignalMetadata

    @staticmethod
    def get_credential_cls() -> t.Type[StopNCIICredentials]:
        return StopNCIICredentials

    @classmethod
    def for_collab(
        cls,
        collab: CollaborationConfigBase,
        credentials: t.Optional[StopNCIICredentials] = None,
    ) -> "StopNCIISignalExchangeAPI":
        credentials = credentials or StopNCIICredentials.get(cls)
        return cls(
            collab,
            api.StopNCIIAPI(credentials.function_key, credentials.subscription_key),
        )

    def fetch_iter(
        self,
        _supported_signal_types: t.Sequence[t.Type[SignalType]],
        checkpoint: t.Optional[StopNCIICheckpoint],
    ) -> t.Iterator[
        state.FetchDelta[
            t.Tuple[str, str],
            StopNCIISignalMetadata,
            StopNCIICheckpoint,
        ]
    ]:
        start_time = api.StopNCIIAPI.DEFAULT_START_TIME
        if checkpoint is not None:
            start_time = checkpoint.update_time
        for result in self.api.fetch_hashes_iter(start_timestamp=start_time):
            translated = (_get_delta_mapping(r) for r in result.hashRecords)
            yield state.FetchDelta(
                dict(t for t in translated if t[0][0]),
                StopNCIICheckpoint.from_stopncii_fetch(result),
            )


def _get_delta_mapping(
    record: api.StopNCIIHashRecord,
) -> t.Tuple[t.Tuple[str, str], t.Optional[StopNCIISignalMetadata]]:

    type_str = _type_mapping().get(record.signalType)
    if not type_str:
        return ("", ""), None

    # If no active cases associated with the hash, should it be deleted?
    if record.hashValue in (
        api.StopNCIICaseStatus.Withdrawn,
        api.StopNCIICaseStatus.Deleted,
    ):
        metadata = None
    else:
        metadata = StopNCIISignalMetadata(record.CSPFeedbacks)

    return ((type_str, record.hashValue), metadata)


@lru_cache(maxsize=1)
def _type_mapping() -> t.Dict[api.StopNCIISignalType, str]:
    return {
        api.StopNCIISignalType.ImagePDQ: PdqSignal.get_name(),
        api.StopNCIISignalType.VideoMD5: VideoMD5Signal.get_name(),
        api.StopNCIISignalType.URL: URLSignal.get_name(),
        api.StopNCIISignalType.Text: RawTextSignal.get_name(),
    }


def _opinion_mapping(fb: api.StopNCIICSPFeedbackValue) -> state.SignalOpinionCategory:
    if fb == api.StopNCIICSPFeedbackValue.Blocked:
        return state.SignalOpinionCategory.POSITIVE_CLASS
    if fb == api.StopNCIICSPFeedbackValue.NotBlocked:
        return state.SignalOpinionCategory.NEGATIVE_CLASS
    return state.SignalOpinionCategory.INVESTIGATION_SEED
