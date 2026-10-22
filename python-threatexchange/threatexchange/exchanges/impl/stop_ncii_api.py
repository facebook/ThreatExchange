# Copyright (c) Meta Platforms, Inc. and affiliates.

"""SignalExchangeAPI implementation for StopNCII.org"""

import datetime
from functools import lru_cache
import logging
import time
import typing as t
from dataclasses import dataclass, field, replace

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

# StopNCII has been observed to return a malformed page for a specific window
# of the FetchHashes stream until fixed on their side (see
# github.com/facebook/ThreatExchange/issues/2004). A malformed page has no
# nextSetTimestamp to continue from, so we skip ahead this far, record the
# skipped window in the checkpoint, and retry it on every later fetch.
MALFORMED_PAGE_SKIP_SEC = 10 * 60
# After this many skips in a row without a good page, stop and raise instead,
# so a fully broken API fails loudly rather than skipping through all time.
MALFORMED_PAGE_MAX_CONSECUTIVE_SKIPS = 12


@dataclass
class StopNCIISkippedWindow:
    """[start, end) of the FetchHashes stream not yet fetched successfully"""

    start: int
    end: int

    def __str__(self) -> str:
        return f"{_timeformat(self.start)} - {_timeformat(self.end)}"


@dataclass
class StopNCIICheckpoint(
    state.FetchCheckpointBase,
):
    update_time: int
    last_fetch_time: int
    # Windows before update_time that were skipped because of malformed
    # pages, oldest first. Retried on every fetch until they succeed.
    skipped_windows: t.List[StopNCIISkippedWindow] = field(default_factory=list)

    def is_stale(self) -> bool:
        """Consider stale after 30d of not fetching"""
        return time.time() - self.last_fetch_time > 3600 * 24 * 30

    def get_progress_timestamp(self) -> t.Optional[int]:
        return self.update_time

    @classmethod
    def from_stopncii_fetch(
        cls,
        response: api.FetchHashesResponse,
        skipped_windows: t.Sequence[StopNCIISkippedWindow] = (),
    ) -> "StopNCIICheckpoint":
        return cls(response.nextSetTimestamp, int(time.time()), list(skipped_windows))


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

    def __str__(self) -> str:
        """
        Specialized override for StopNCII.

        For StopNCII, we "unowned" signals submitted by users, as well as well-formed
        owner names.
        """
        confidence = 0
        owner_strs = []

        for feedback in sorted(self.feedbacks, key=lambda f: f.source):
            if feedback.feedbackValue == api.StopNCIICSPFeedbackValue.Blocked:
                confidence += 1
                owner_strs.append(f"+{feedback.source}")
            elif feedback.feedbackValue == api.StopNCIICSPFeedbackValue.NotBlocked:
                confidence -= 1
                owner_strs.append(f"-{feedback.source}")

        confidence_str = f"{confidence:+d}" if owner_strs else str(confidence)

        return f"{self.get_as_aggregate_opinion().category.name} {confidence_str} {','.join(owner_strs)}"


@dataclass
class StopNCIICredentials(auth.CredentialHelper):
    ENV_VARIABLE: t.ClassVar[str] = "TX_STOPNCII_KEYS"
    FILE_NAME: t.ClassVar[str] = "~/.tx_stopncii_keys"

    fetch_function_key: str = field(
        metadata={
            "help": "API key for the Fetch Hashes endpoint. Used when downloading hashes from StopNCII."
        }
    )
    subscription_key: str = field(
        metadata={
            "help": "Azure API Management subscription key. Sent as Ocp-Apim-Subscription-Key on all requests."
        }
    )
    base_url_override: t.Optional[str] = field(
        default=None,
        metadata={
            "help": "Optional. Override the API base URL (e.g. for testing). Leave blank to use https://api.stopncii.org/v1"
        },
    )

    @classmethod
    def _from_str(cls, s: str) -> "StopNCIICredentials":
        parts = s.strip().split(",")
        if len(parts) == 2:
            fetch_function_key, subscription_key = parts
            base_url_override = None
        elif len(parts) == 3:
            fetch_function_key, subscription_key, base_url_override = parts
        else:
            raise ValueError(
                "Invalid stopNCII credentials format. Should be 'function_key,subscription_key' OR 'function_key_subscription_key,base_url_override'."
            )

        return cls(
            subscription_key=subscription_key,
            fetch_function_key=fetch_function_key,
            base_url_override=base_url_override,
        )

    def _are_valid(self) -> bool:
        return bool(self.fetch_function_key and self.subscription_key)


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
            api.StopNCIIAPI(
                credentials.subscription_key,
                credentials.fetch_function_key,
                base_url_override=credentials.base_url_override,
            ),
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
        skipped: t.List[StopNCIISkippedWindow] = []
        if checkpoint is not None:
            start_time = checkpoint.update_time
            # Copied, since we modify them and they are shared with checkpoints
            skipped = [replace(w) for w in checkpoint.skipped_windows]

        # Retry earlier skipped windows first, so once StopNCII fixes their
        # data, it gets fetched without any action from whoever runs this.
        for window in list(skipped):
            yield from self._fetch_skipped_window(window, start_time, skipped)

        position = start_time
        consecutive_skips = 0
        while True:
            try:
                for result in self.api.fetch_hashes_iter(start_timestamp=position):
                    consecutive_skips = 0
                    position = result.nextSetTimestamp
                    yield _to_delta(result, _checkpoint(position, skipped))
                return
            except api.StopNCIIMalformedResponseError:
                consecutive_skips += 1
                now = int(time.time())
                if (
                    consecutive_skips > MALFORMED_PAGE_MAX_CONSECUTIVE_SKIPS
                    or position >= now
                ):
                    raise
            # Never skip past now, or records changed after the skip could
            # be missed when the window is later fetched successfully.
            window = StopNCIISkippedWindow(
                position, min(position + MALFORMED_PAGE_SKIP_SEC, now)
            )
            if skipped and skipped[-1].end == window.start:
                skipped[-1].end = window.end
            else:
                skipped.append(window)
            logging.error(
                "StopNCII returned a malformed page, skipping %s. "
                "It will be retried on every later fetch until it succeeds.",
                window,
            )
            position = window.end
            yield state.FetchDelta({}, _checkpoint(position, skipped))
            if position >= now:
                return

    def _fetch_skipped_window(
        self,
        window: StopNCIISkippedWindow,
        update_time: int,
        skipped: t.List[StopNCIISkippedWindow],
    ) -> t.Iterator[
        state.FetchDelta[
            t.Tuple[str, str],
            StopNCIISignalMetadata,
            StopNCIICheckpoint,
        ]
    ]:
        """
        Fetch a previously skipped window, removing it from skipped once done.

        On partial progress, the window is shrunk to what is left. Records
        are the current snapshot, so fetching them late won't overwrite
        newer data with stale data.
        """
        original = str(window)
        try:
            for result in self.api.fetch_hashes_iter(start_timestamp=window.start):
                # If there are no more records, everything up to now has been
                # fetched, and a window never extends past when it was skipped.
                if result.nextSetTimestamp >= window.end or not result.hasMoreRecords:
                    skipped.remove(window)
                    logging.info("StopNCII fetched previously skipped %s", original)
                    yield _to_delta(result, _checkpoint(update_time, skipped))
                    return
                window.start = max(window.start, result.nextSetTimestamp)
                yield _to_delta(result, _checkpoint(update_time, skipped))
        except api.StopNCIIMalformedResponseError:
            logging.warning(
                "StopNCII still returns a malformed page for previously skipped %s, "
                "will retry on the next fetch",
                window,
            )


def _checkpoint(
    update_time: int, skipped: t.Sequence[StopNCIISkippedWindow]
) -> StopNCIICheckpoint:
    return StopNCIICheckpoint(
        update_time, int(time.time()), [replace(w) for w in skipped]
    )


def _to_delta(
    result: api.FetchHashesResponse, checkpoint: StopNCIICheckpoint
) -> state.FetchDelta[
    t.Tuple[str, str],
    StopNCIISignalMetadata,
    StopNCIICheckpoint,
]:
    translated = (_get_delta_mapping(r) for r in result.hashRecords)
    return state.FetchDelta(dict(t for t in translated if t[0][0]), checkpoint)


def _timeformat(timestamp: int) -> str:
    return datetime.datetime.fromtimestamp(
        timestamp, tz=datetime.timezone.utc
    ).isoformat()


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
