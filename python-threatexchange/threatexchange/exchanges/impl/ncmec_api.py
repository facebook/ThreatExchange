# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
SignalExchangeAPI impl for the NCMEC hash exchange API

@see NCMECSignalExchangeAPI
"""


import logging
import typing as t
from dataclasses import dataclass, field

from threatexchange.exchanges.clients.ncmec import hash_api as api

from threatexchange.exchanges import fetch_state as state
from threatexchange.exchanges import signal_exchange_api
from threatexchange.exchanges.collab_config import (
    CollaborationConfigBase,
    CollaborationConfigWithDefaults,
)
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal


_API_NAME: str = "ncmec"


@dataclass
class NCMECCheckpoint(
    state.FetchCheckpointBase,
):
    """
    NCMEC primarily revolves around polling the timestamp.

    NCMEC IDs seem to stay around forever, so no need for is_stale()
    """

    max_timestamp: int

    def get_progress_timestamp(self) -> t.Optional[int]:
        return self.max_timestamp

    @classmethod
    def from_ncmec_fetch(cls, response: api.GetEntriesResponse) -> "NCMECCheckpoint":
        return cls(response.max_timestamp)


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
class NCMECSignalMetadata(state.FetchedSignalMetadata):
    """
    NCMEC metadata includes who uploaded it, as well as what they tagged.

    The NCMEC API has no concept of false positives - every entry is reported.
    """

    member_entries: t.Dict[int, t.Set[str]]

    def get_as_opinions(self) -> t.List[state.SignalOpinion]:
        return [
            state.SignalOpinion(
                member_id, state.SignalOpinionCategory.TRUE_POSITIVE, tags
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


class NCMECSignalExchangeAPI(
    signal_exchange_api.SignalExchangeAPI[
        NCMECCollabConfig,
        NCMECCheckpoint,
        NCMECSignalMetadata,
        str,
        api.NCMECEntryUpdate,
    ]
):
    """
    Conversion for the NCMEC hash API

    Key implementation details:
        1. API is a stream of content: opinion, hashes,
           which need to be remapped to hash => opinion
        2. Owners have ids
        3. As of 5/2022 there are no false positive or seen statuses
    """

    def __init__(
        self,
        username: str = "",
        password: str = "",
    ) -> None:
        super().__init__()
        self._api = None
        if username and password:
            self._api = api.NCMECHashAPI(
                username,
                password,
            )

    @classmethod
    def get_name(cls) -> str:
        return _API_NAME

    @classmethod
    def get_config_class(cls) -> t.Type[NCMECCollabConfig]:
        return NCMECCollabConfig

    @classmethod
    def get_checkpoint_cls(cls) -> t.Type[NCMECCheckpoint]:
        return NCMECCheckpoint

    @classmethod
    def get_record_cls(cls) -> t.Type[NCMECSignalMetadata]:
        return NCMECSignalMetadata

    @property
    def client(self) -> api.NCMECHashAPI:
        if self._api is None:
            raise Exception("NCMEC username and password not configured.")
        return self._api

    def fetch_iter(
        self,
        _supported_signal_types: t.Sequence[t.Type[SignalType]],
        collab: NCMECCollabConfig,
        checkpoint: t.Optional[NCMECCheckpoint],
    ) -> t.Iterator[state.FetchDelta[str, api.NCMECEntryUpdate, NCMECCheckpoint]]:
        start_time = 0
        if checkpoint is not None:
            start_time = checkpoint.max_timestamp
        for result in self.client.get_entries_iter(start_timestamp=start_time):
            updates = result.updates
            if collab.only_esp_ids:
                updates = [
                    entry for entry in updates if entry.member_id in collab.only_esp_ids
                ]
            yield state.FetchDelta(
                {f"{entry.member_id}-{entry.id}": entry for entry in updates},
                NCMECCheckpoint.from_ncmec_fetch(result),
            )

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
        fetched: t.Mapping[str, api.NCMECEntryUpdate],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, NCMECSignalMetadata]]:
        mapping: t.Mapping[
            t.Tuple[api.NCMECEntryType, str], t.Type[SignalType]
        ] = _get_conversion(signal_types)
        ret: t.Dict[t.Type[SignalType], t.Dict[str, NCMECSignalMetadata]] = {}
        for entry in fetched.values():
            if entry.deleted:
                continue  # We expect len(fingerprints) == 0 here, but to be safe
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
