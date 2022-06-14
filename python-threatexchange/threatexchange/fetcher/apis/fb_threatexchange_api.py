# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
SignalExchangeAPI impl for Facebook/Meta's ThreatExchange Graph API platform.

https://developers.facebook.com/programs/threatexchange
https://developers.facebook.com/docs/threat-exchange/reference/apis/
"""


import typing as t
import time
from dataclasses import dataclass, field
from threatexchange.fb_threatexchange.threat_updates import ThreatUpdateJSON

from threatexchange.fb_threatexchange.api import ThreatExchangeAPI, _CursoredResponse

from threatexchange.fetcher import fetch_state as state
from threatexchange.fetcher.fetch_api import (
    SignalExchangeAPIWithSimpleUpdates,
)
from threatexchange.fetcher.collab_config import CollaborationConfigWithDefaults
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.fetcher.apis.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)

_API_NAME = "fb_threat_exchange"


@dataclass
class _FBThreatExchangeCollabConfigRequiredFields:
    privacy_group: int


@dataclass
class FBThreatExchangeCollabConfig(
    CollaborationConfigWithDefaults,
    _FBThreatExchangeCollabConfigRequiredFields,
):
    api: str = field(init=False, default=_API_NAME)
    app_token_override: t.Optional[str] = None


@dataclass
class FBThreatExchangeCheckpoint(state.FetchCheckpointBase):
    """
    State about the progress of a /threat_updates-backed state.

    If a client does not resume tailing the threat_updates endpoint fast enough,
    deletion records will be removed, making it impossible to determine which
    records should be retained without refetching the entire dataset from scratch.
    """

    update_time: int = 0
    last_fetch_time: int = field(default_factory=lambda: int(time.time()))

    def is_stale(self) -> bool:
        """
        The API implementation will retain for 90 days

        https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-updates/
        """
        return time.time() - self.last_fetch_time > 3600 * 24 * 85  # 85 days

    def get_progress_timestamp(self) -> int:
        return self.update_time


@dataclass
class FBThreatExchangeOpinion(state.SignalOpinion):

    REACTION_DESCRIPTOR_ID: t.ClassVar[int] = -1

    descriptor_id: t.Optional[int]


@dataclass
class FBThreatExchangeIndicatorRecord(state.FetchedSignalMetadata):

    opinions: t.List[FBThreatExchangeOpinion]

    def get_as_opinions(  # type: ignore  # Why can't mypy tell this is a subclass?
        self,
    ) -> t.List[FBThreatExchangeOpinion]:
        return self.opinions

    @classmethod
    def from_threatexchange_json(
        cls, te_json: ThreatUpdateJSON
    ) -> t.Optional["FBThreatExchangeIndicatorRecord"]:
        if te_json.should_delete:
            return None

        explicit_opinions = {}
        implicit_opinions = {}

        for td_json in te_json.raw_json["descriptors"]["data"]:
            td_id = int(td_json["id"])
            owner_id = int(td_json["owner"]["id"])
            status = (td_json["status"],)
            # added_on = td_json["added_on"]
            tags = td_json.get("tags", [])
            # This is needed because ThreatExchangeAPI.get_threat_descriptors()
            # does a transform, but other locations do not
            if isinstance(tags, dict):
                tags = sorted(tag["text"] for tag in tags["data"])

            category = state.SignalOpinionCategory.WORTH_INVESTIGATING

            if status == "MALICIOUS":
                category = state.SignalOpinionCategory.TRUE_POSITIVE
            elif status == "NON_MALICIOUS":
                category = state.SignalOpinionCategory.FALSE_POSITIVE

            explicit_opinions[owner_id] = FBThreatExchangeOpinion(
                owner_id, category, tags, td_id
            )

            for reaction in td_json.get("reactions", []):
                rxn = reaction["key"]
                owner = int(reaction["value"])
                if rxn == "HELPFUL":
                    implicit_opinions[owner] = state.SignalOpinionCategory.TRUE_POSITIVE
                elif rxn == "DISAGREE_WITH_TAGS" and owner not in implicit_opinions:
                    implicit_opinions[
                        owner
                    ] = state.SignalOpinionCategory.FALSE_POSITIVE

        for owner_id, category in implicit_opinions.items():
            if owner_id in explicit_opinions:
                continue
            explicit_opinions[owner_id] = FBThreatExchangeOpinion(
                owner_id,
                category,
                set(),
                FBThreatExchangeOpinion.REACTION_DESCRIPTOR_ID,
            )

        if not explicit_opinions:
            # Visibility bug of some kind on TE API :(
            return None
        return cls(list(explicit_opinions.values()))

    @staticmethod
    def te_threat_updates_fields() -> t.Tuple[str, ...]:
        """The input to the "field" selector for the API"""
        return (
            "indicator",
            "type",
            "last_updated",
            "should_delete",
            "descriptors{%s}"
            % ",".join(
                (
                    "id",
                    "reactions",
                    "owner{id}",
                    "tags",
                    "status",
                )
            ),
        )


ThreatExchangeDelta = state.FetchDelta[
    t.Dict[t.Tuple[str, str], t.Optional[FBThreatExchangeIndicatorRecord]],
    FBThreatExchangeCheckpoint,
]


class FBThreatExchangeSignalExchangeAPI(
    SignalExchangeAPIWithSimpleUpdates[
        FBThreatExchangeCollabConfig,
        FBThreatExchangeCheckpoint,
        FBThreatExchangeIndicatorRecord,
    ]
):
    def __init__(self, fb_app_token: t.Optional[str] = None) -> None:
        self._api = None
        if fb_app_token is not None:
            self._api = ThreatExchangeAPI(fb_app_token)

    @property
    def api(self) -> ThreatExchangeAPI:
        if self._api is None:
            raise Exception("App Developer token not configured.")
        return self._api

    @classmethod
    def get_name(cls) -> str:
        return _API_NAME

    @classmethod
    def get_checkpoint_cls(cls) -> t.Type[FBThreatExchangeCheckpoint]:
        return FBThreatExchangeCheckpoint

    @classmethod
    def get_record_cls(cls) -> t.Type[FBThreatExchangeIndicatorRecord]:
        return FBThreatExchangeIndicatorRecord

    @classmethod
    def get_config_class(cls) -> t.Type[FBThreatExchangeCollabConfig]:
        return FBThreatExchangeCollabConfig

    def resolve_owner(self, id: int) -> str:
        # TODO -This is supported by the API
        raise NotImplementedError

    def get_own_owner_id(self, collab: FBThreatExchangeCollabConfig) -> int:
        return self.api.app_id

    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        collab: FBThreatExchangeCollabConfig,
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[FBThreatExchangeCheckpoint],
    ) -> t.Iterator[ThreatExchangeDelta]:
        start_time = None if checkpoint is None else checkpoint.update_time
        cursor = self.api.get_threat_updates(
            collab.privacy_group,
            start_time=start_time,
            page_size=500,
            fields=ThreatUpdateJSON.te_threat_updates_fields(),
            decode_fn=ThreatUpdateJSON,
        )

        batch: t.List[ThreatUpdateJSON] = []
        highest_time = 0
        for fetch in cursor:
            for update in fetch:
                # TODO catch errors here
                batch.append(update)
                # Is supposed to be strictly increasing
                highest_time = max(update.time, highest_time)

            # TODO - We can clobber types that map into multiple
            type_mapping = _make_indicator_type_mapping(supported_signal_types)
            updates = {}
            for u in batch:
                st = type_mapping.get(u.threat_type)
                if st is not None:
                    updates[
                        st.get_name(), u.indicator
                    ] = FBThreatExchangeIndicatorRecord.from_threatexchange_json(u)

            yield ThreatExchangeDelta(
                updates,
                FBThreatExchangeCheckpoint(highest_time),
            )

    def report_seen(
        self,
        collab: FBThreatExchangeCollabConfig,
        s_type: SignalType,
        signal: str,
        metadata: FBThreatExchangeIndicatorRecord,
    ) -> None:
        # TODO - this is supported by the API
        raise NotImplementedError

    def report_opinion(
        self,
        collab: FBThreatExchangeCollabConfig,
        s_type: t.Type[SignalType],
        signal: str,
        opinion: state.SignalOpinion,
    ) -> None:
        # TODO - this is supported by the API
        raise NotImplementedError

    def report_true_positive(
        self,
        collab: FBThreatExchangeCollabConfig,
        s_type: t.Type[SignalType],
        signal: str,
        metadata: FBThreatExchangeIndicatorRecord,
    ) -> None:
        # TODO - this is supported by the API
        self.report_opinion(
            collab,
            s_type,
            signal,
            state.SignalOpinion(
                owner=self.get_own_owner_id(collab),
                category=state.SignalOpinionCategory.TRUE_POSITIVE,
                tags=set(),
            ),
        )

    def report_false_positive(
        self,
        collab: FBThreatExchangeCollabConfig,
        s_type: t.Type[SignalType],
        signal: str,
        _metadata: FBThreatExchangeIndicatorRecord,
    ) -> None:
        self.report_opinion(
            collab,
            s_type,
            signal,
            state.SignalOpinion(
                owner=self.get_own_owner_id(collab),
                category=state.SignalOpinionCategory.FALSE_POSITIVE,
                tags=set(),
            ),
        )


def _make_indicator_type_mapping(
    supported_signal_types: t.Sequence[t.Type[SignalType]],
) -> t.Dict[str, t.Type[SignalType]]:
    # TODO - We can clobber types that map into multiple
    type_mapping: t.Dict[str, t.Type[SignalType]] = {}
    for st in supported_signal_types:
        if issubclass(st, HasFbThreatExchangeIndicatorType):
            types = st.INDICATOR_TYPE
            if isinstance(types, str):
                types = (types,)
            type_mapping.update((t, st) for t in types)
        else:
            # Setdefault here to prefer names claimed by above
            type_mapping.setdefault(st.get_name().upper(), st)
    return type_mapping
