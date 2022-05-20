# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
SignalExchangeAPI impl for the NCMEC hash exchange

"""


import time
import typing as t
from dataclasses import dataclass
from threatexchange.fetcher.simple.state import (
    SimpleFetchDelta,
)

from threatexchange.ncmec import hash_api as api

from threatexchange.fetcher import fetch_state as state
from threatexchange.fetcher import fetch_api
from threatexchange.fetcher.collab_config import (
    CollaborationConfigBase,
    CollaborationConfigWithDefaults,
)
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.md5 import VideoMD5Signal


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
        return cls(response.max_timestamp, int(time.time()))


class NCMECCollaboration(CollaborationConfigWithDefaults, CollaborationConfigBase):
    environment: api.NCMECEnvironment


# @dataclass
# class NCMECCspOpinion(state.SignalOpinion):
#     ids: t.Set[str]
#     category: state.SignalOpinionCategory = field(
#         default=state.SignalOpinionCategory.TRUE_POSITIVE, init=False
#     )


# @dataclass
# class NCMECHashMetadata(state.FetchedSignalMetadata):

#     opinions: t.List[NCMECCspOpinion]

#     def get_as_opinions(self) -> t.List[state.SignalOpinion]:
#         return self.opinions


@dataclass
class _NCMECEntryMetadata(state.FetchedSignalMetadata):
    """
    Placeholder to store entries from the API

    TODO: It turns out I was not smart enough and build the API interface
          poorly, which NCMEC has exposed.
          The chain of Delta => Dict[(type, hash): ?Metadata] => Store => Index
          breaks because NCME doesn't map easily to a unique (type, hash) pairing.
          Instead, it has its own unique keys (esp_id, entry_id).

          The fix is to seperate out the concerns needed for UpdateDelta to work
          (any unique key, a combining function) from the concerns needed for Index
          to work (group by signal type => Metadata).
    """

    entry: api.NCMECEntryUpdate

    def get_as_opinions(self) -> t.List[state.SignalOpinion]:
        raise NotImplementedError(
            "Placeholder while I figure out the correct model for NCMEC"
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


class NCMECSignalExchangeAPI(fetch_api.SignalExchangeAPIWithIterFetch[NCMECCheckpoint]):
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

    @property
    def api(self) -> api.NCMECHashAPI:
        if self._api is None:
            raise Exception("NCMEC username and password not configured.")
        return self._api

    def fetch_iter(
        self,
        _supported_signal_types: t.List[t.Type[SignalType]],
        _collab: CollaborationConfigBase,
        checkpoint: t.Optional[NCMECCheckpoint],
    ) -> t.Iterator[SimpleFetchDelta[NCMECCheckpoint, NCMECSignalMetadata]]:
        start_time = 0
        if checkpoint is not None:
            start_time = checkpoint.max_timestamp
        for result in self.api.get_entries_iter(start_timestamp=start_time):
            translated = (_get_update_mapping(u) for u in result.updates)
            yield SimpleFetchDelta(
                dict(t for t in translated if t[0][0]),
                NCMECCheckpoint.from_ncmec_fetch(result),
                done=not result.next,
            )


def _get_update_mapping(
    entry: api.NCMECEntryUpdate,
) -> t.Tuple[t.Tuple[str, str], t.Optional[_NCMECEntryMetadata]]:
    metadata = None
    if not entry.deleted:
        metadata = _NCMECEntryMetadata(entry)
    return ((str(entry.member_id), entry.id), metadata)
