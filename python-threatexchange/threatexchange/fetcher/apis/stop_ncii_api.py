# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
SignalExchangeAPI impl StopNCII.org

"""


from functools import lru_cache
import time
import typing as t
from dataclasses import dataclass

from threatexchange.stopncii import api

from threatexchange.fetcher import fetch_state as state
from threatexchange.fetcher import fetch_api
from threatexchange.fetcher.collab_config import (
    CollaborationConfigBase,
)
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.pdq import PdqSignal
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

    def get_as_opinions(self) -> t.List[state.SignalOpinion]:
        opinions = [
            state.SignalOpinion(-1, _opinion_mapping(f.feedbackValue), f.tags)
            for f in self.feedbacks
        ]
        # implicitly, all records from StopNCII are from user-submitted cases
        opinions.append(
            state.SignalOpinion(
                0, state.SignalOpinionCategory.WORTH_INVESTIGATING, set()
            ),
        )
        return opinions


class StopNCIISignalExchangeAPI(
    fetch_api.SignalExchangeAPIWithSimpleUpdates[
        CollaborationConfigBase,
        StopNCIICheckpoint,
        StopNCIISignalMetadata,
    ]
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
        subscription_key: t.Optional[str],
        fetch_function_key: t.Optional[str],
        additional_function_keys: t.Optional[t.Dict[api.StopNCIIEndpoint, str]] = None,
    ) -> None:
        super().__init__()
        self._api = None
        if subscription_key is not None and fetch_function_key is not None:
            self._api = api.StopNCIIAPI(
                subscription_key,
                fetch_function_key,
                additional_function_keys,
            )

    @property
    def api(self) -> api.StopNCIIAPI:
        if self._api is None:
            raise Exception("StopNCII.org access tokens not configured.")
        return self._api

    def fetch_iter(
        self,
        _supported_signal_types: t.Sequence[t.Type[SignalType]],
        _collab: CollaborationConfigBase,
        checkpoint: t.Optional[StopNCIICheckpoint],
    ) -> t.Iterator[
        state.FetchDelta[
            t.Dict[t.Tuple[str, str], t.Optional[StopNCIISignalMetadata]],
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
        return state.SignalOpinionCategory.TRUE_POSITIVE
    if fb == api.StopNCIICSPFeedbackValue.NotBlocked:
        return state.SignalOpinionCategory.FALSE_POSITIVE
    return state.SignalOpinionCategory.WORTH_INVESTIGATING
