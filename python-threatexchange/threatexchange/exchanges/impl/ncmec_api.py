# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
SignalExchangeAPI impl for the NCMEC hash exchange API

@see NCMECSignalExchangeAPI
"""


import logging
import time
import typing as t
from dataclasses import dataclass, field

from threatexchange.exchanges.clients.ncmec import hash_api as api

from threatexchange.exchanges import auth, fetch_state as state
from threatexchange.exchanges import signal_exchange_api
from threatexchange.exchanges.collab_config import (
    CollaborationConfigWithDefaults,
)
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq.signal import PdqSignal


_API_NAME: str = "ncmec"


@dataclass
class NCMECCheckpoint(
    state.FetchCheckpointBase,
):
    """
    NCMEC primarily revolves around polling the timestamp.

    NCMEC IDs seem to stay around forever, so no need for is_stale()
    """

    # The biggest value of "to", and the next "from"
    get_entries_max_ts: int

    def get_progress_timestamp(self) -> t.Optional[int]:
        return self.get_entries_max_ts

    @classmethod
    def from_ncmec_fetch(cls, response: api.GetEntriesResponse) -> "NCMECCheckpoint":
        return cls(response.max_timestamp)

    def __setstate__(self, d: t.Dict[str, t.Any]) -> None:
        """Implemented for pickle version compatibility."""
        # 0.99.0 => 1.0.0:
        ### field 'max_timestamp' renamed to 'get_entries_max_ts'
        if "max_timestamp" in d:
            d["get_entries_max_ts"] = d.pop("max_timestamp")
        self.__dict__ = d


@dataclass
class _NCMECCollabConfigRequiredFields:
    environment: api.NCMECEnvironment = field(
        metadata={"help": "which database to connect to"}
    )


@dataclass
class NCMECCollabConfig(
    CollaborationConfigWithDefaults,
    _NCMECCollabConfigRequiredFields,
):
    api: str = field(init=False, default=_API_NAME)
    only_esp_ids: t.Set[int] = field(
        default_factory=set,
        metadata={
            "help": "Only take entries from these eletronic service provider (ESP) ids"
        },
    )


@dataclass
class NCMECOpinion(state.SignalOpinion):
    esp_id: int

    def __setstate__(self, d: t.Dict[str, t.Any]) -> None:
        """Implemented for pickle version compatibility."""
        # 0.99.0 => 1.0.0:
        ### field 'owner_id' renamed to 'esp_id'
        if "owner" in d:
            d["esp_id"] = d["owner"]
        super().__setstate__(d)


@dataclass
class NCMECSignalMetadata(state.FetchedSignalMetadata):
    """
    NCMEC metadata includes who uploaded it, as well as what they tagged.

    The NCMEC API has no concept of false positives - every entry is reported.
    """

    member_entries: t.Dict[int, t.Set[str]]

    def get_as_opinions(self) -> t.Sequence[NCMECOpinion]:
        return [
            NCMECOpinion(
                False,  # TODO - get my own esp_id
                state.SignalOpinionCategory.POSITIVE_CLASS,
                tags,
                member_id,
            )
            for member_id, tags in self.member_entries.items()
        ]


def _get_conversion(
    signal_types: t.Sequence[t.Type[SignalType]],
) -> t.Mapping[t.Tuple[api.NCMECEntryType, str], t.Type[SignalType]]:
    ret: t.Dict[t.Tuple[api.NCMECEntryType, str], t.Type[SignalType]] = {}
    if VideoMD5Signal in signal_types:
        ret[api.NCMECEntryType.video, "md5"] = VideoMD5Signal
    if PdqSignal in signal_types:
        ret[api.NCMECEntryType.image, "pdq"] = PdqSignal
    for st in signal_types:
        if st.get_name() == "photodna":
            ret[api.NCMECEntryType.image, "pdna"] = st
            break
    return ret


@dataclass
class NCMECCredentials(auth.CredentialHelper):
    ENV_VARIABLE: t.ClassVar[str] = "TX_NCMEC_CREDENTIALS"
    FILE_NAME: t.ClassVar[str] = "~/.tx_ncmec_credentials"

    user: str
    password: str

    @classmethod
    def _from_str(cls, s: str) -> "NCMECCredentials":
        user, _, passw = s.strip().partition(":")
        return cls(user, passw)

    def _are_valid(self) -> bool:
        return bool(self.user and self.password)


class NCMECSignalExchangeAPI(
    auth.SignalExchangeWithAuth[NCMECCollabConfig, NCMECCredentials],
    signal_exchange_api.SignalExchangeAPI[
        NCMECCollabConfig,
        NCMECCheckpoint,
        NCMECSignalMetadata,
        str,
        api.NCMECEntryUpdate,
    ],
):
    """
    Conversion for the NCMEC hash API

    Key implementation details:
        1. API is a stream of content: opinion, hashes,
           which need to be remapped to hash => opinion
        2. Owners have ids
        3. As of 5/2022 there are no false positive or seen statuses
    """

    MAX_FETCH_SIZE: t.ClassVar[int] = 400000
    FETCH_SHRINK_FACTOR: t.ClassVar[int] = 4

    def __init__(
        self,
        collab: NCMECCollabConfig,
        username: str,
        password: str,
    ) -> None:
        super().__init__()
        self.collab = collab
        self._username = username
        self._password = password

    @classmethod
    def for_collab(
        cls,
        collab: NCMECCollabConfig,
        credentials: t.Optional["NCMECCredentials"] = None,
    ) -> "NCMECSignalExchangeAPI":
        credentials = credentials or NCMECCredentials.get(cls)
        return cls(collab, credentials.user, credentials.password)

    @classmethod
    def get_name(cls) -> str:
        return _API_NAME

    @staticmethod
    def get_config_cls() -> t.Type[NCMECCollabConfig]:
        return NCMECCollabConfig

    @staticmethod
    def get_checkpoint_cls() -> t.Type[NCMECCheckpoint]:
        return NCMECCheckpoint

    @staticmethod
    def get_record_cls() -> t.Type[NCMECSignalMetadata]:
        return NCMECSignalMetadata

    @staticmethod
    def get_credential_cls() -> t.Type[NCMECCredentials]:
        return NCMECCredentials

    def get_client(self, environment: api.NCMECEnvironment) -> api.NCMECHashAPI:
        if not api.is_valid_user_pass(self._username, self._password):
            raise Exception("NCMEC username and password not configured or invalid.")
        return api.NCMECHashAPI(self._username, self._password, environment)

    def fetch_iter(
        self,
        _supported_signal_types: t.Sequence[t.Type[SignalType]],
        checkpoint: t.Optional[NCMECCheckpoint],
    ) -> t.Iterator[state.FetchDelta[str, api.NCMECEntryUpdate, NCMECCheckpoint]]:
        """
        Use flow control to efficiently fetch from the NCMEC API.

        The NCMEC API does not provide entries in a strictly ascending time order.
        As a result, the only checkpoint we can safely return is if we have
        exhausted an entire time range of fetching.

        However, the data within the NCMEC hash dbs are randomly distributed,
        with the following observed behavior:
            1. Fetching an empty range (0 entries) is fast
            2. We can estimate the number of entries in a range based on the
               parameters of the "next" field
            3. Fetching from a cursor of data is significantly faster than
               generating a new cursor.

        Therefore, we can aim for the following strategy:
            1. Prefer fetching empty ranges repeatedly rather than potentially
               generating an overfetch. (Shrink quickly, grow slowly)
            2. Be very generous with overfetch limits, since if we've generated
               the cursor
        """
        start_time = 0
        if checkpoint is not None:
            start_time = checkpoint.get_entries_max_ts
        # Avoid being exactly at end time for updates showing up multiple
        # times in the fetch, since entries are not ordered by time
        end_time = int(time.time()) - 5

        client = self.get_client(self.collab.environment)
        # We could probably mutate start time, but new variable for clarity
        current_start = start_time
        # The range we are fetching
        duration = end_time - current_start
        # A counter for when we want to increase our duration
        # We want to be conservative
        low_fetch_counter = 0

        def log(event: str) -> None:
            """Helper to log fetch events"""
            if duration < 1800:
                duration_str = f"{duration} seconds"
            elif duration < 43200:
                duration_str = f"{duration / 3600:.2f} hours"
            else:
                duration_str = f"{duration / (3600 * 24):.2f} days"
            logging.info(
                "NCMEC API %s @%s (%s)",
                event,
                api._date_format(current_start),
                duration_str,
            )

        while current_start < end_time:
            duration = max(1, duration)  # Infinite loop defense
            # Don't fetch past our designated end
            current_end = min(end_time, current_start + duration)
            updates: t.List[api.NCMECEntryUpdate] = []
            for i, entry in enumerate(
                client.get_entries_iter(
                    start_timestamp=current_start, end_timestamp=current_end
                )
            ):
                if i == 0:  # First batch, check for overfetch
                    if (
                        entry.estimated_entries_in_range > self.MAX_FETCH_SIZE
                        and duration > 1
                    ):
                        log(
                            f"est {entry.estimated_entries_in_range} is over max fetch, duration reduced"
                        )
                        # We want to at last shrink by our shrink factor
                        duration = min(
                            duration // self.FETCH_SHRINK_FACTOR,
                            # Especially in early fetches, we are overfetching
                            # by a huge amount, so shrink in proportion to overfetch
                            duration
                            * self.MAX_FETCH_SIZE
                            // entry.estimated_entries_in_range,
                        )
                        low_fetch_counter = 0  # Don't grow right after a shrink
                        break  # Retry get_entries_iter with new parameters
                    else:
                        # Our entry estimatation (based on the cursor parameters)
                        # occasionally seem to over-estimate
                        log(f"est {entry.estimated_entries_in_range} entries")
                elif i % 100 == 0:
                    # If we get down to one second, we can potentially be
                    # fetching an arbitrary large amount of data in one go,
                    # so log something occasionally
                    log(f"large fetch ({i}), up to {len(updates)}")
                updates.extend(entry.updates)
            else:  # AKA a successful fetch
                # If we're hovering near the single-fetch limit for a period
                # of time, we can likely safely expand our range.
                if len(updates) < api.NCMECHashAPI.ENTRIES_PER_FETCH * 2:
                    low_fetch_counter += 1
                    if low_fetch_counter >= self.FETCH_SHRINK_FACTOR:
                        log("multiple low fetches, increasing duration")
                        # Grow slower than we shrink
                        duration *= self.FETCH_SHRINK_FACTOR // 2
                        low_fetch_counter = 0
                # If we are not quite at our limit, but getting close to it,
                # pre-emptively shrink to try and stay under the limit
                elif len(updates) > self.MAX_FETCH_SIZE / self.FETCH_SHRINK_FACTOR:
                    log("close to overfetch limit, reducing duration")
                    duration //= self.FETCH_SHRINK_FACTOR
                    low_fetch_counter = 0
                else:  # Not too small, not too large, just right
                    low_fetch_counter = 0
                yield state.FetchDelta(
                    {f"{entry.member_id}-{entry.id}": entry for entry in updates},
                    NCMECCheckpoint(current_end),
                )
                current_start = current_end

    @classmethod
    def fetch_value_merge(
        cls,
        old: t.Optional[api.NCMECEntryUpdate],
        new: t.Optional[api.NCMECEntryUpdate],
    ) -> t.Optional[api.NCMECEntryUpdate]:
        assert new is not None, "fetch shouldn't do this"
        if new.deleted:
            return None
        return new

    @classmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        collab: NCMECCollabConfig,
        fetched: t.Mapping[str, api.NCMECEntryUpdate],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, NCMECSignalMetadata]]:
        mapping: t.Mapping[
            t.Tuple[api.NCMECEntryType, str], t.Type[SignalType]
        ] = _get_conversion(signal_types)
        ret: t.Dict[t.Type[SignalType], t.Dict[str, NCMECSignalMetadata]] = {}
        for entry in fetched.values():
            if entry.deleted:
                continue  # We expect len(fingerprints) == 0 here, but to be safe
            if collab.only_esp_ids and entry.member_id not in collab.only_esp_ids:
                continue
            for fingerprint_type, fingerprint_value in entry.fingerprints.items():
                st = mapping.get((entry.entry_type, fingerprint_type))
                if st is not None:
                    try:
                        signal_value = st.validate_signal_str(fingerprint_value)
                    except Exception:
                        logging.warning(
                            "Invalid fingerprint (%s): %s",
                            st.get_name(),
                            fingerprint_value,
                        )
                        continue
                    metadata = ret.setdefault(st, {}).setdefault(
                        signal_value, NCMECSignalMetadata({})
                    )
                    tags = metadata.member_entries.setdefault(entry.member_id, set())
                    if entry.classification:
                        tags.add(entry.classification)
        return ret
