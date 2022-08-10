# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
SignalExchangeAPI impl for Facebook/Meta's ThreatExchange Graph API platform.

https://developers.facebook.com/programs/threatexchange
https://developers.facebook.com/docs/threat-exchange/reference/apis/
"""


from collections import defaultdict
import typing as t
import time
from dataclasses import dataclass, field
from threatexchange.exchanges.clients.fb_threatexchange.threat_updates import (
    ThreatUpdateJSON,
)

from threatexchange.exchanges.clients.fb_threatexchange.api import (
    ThreatExchangeAPI,
    is_valid_app_token,
)

from threatexchange.exchanges import auth, fetch_state as state
from threatexchange.exchanges.signal_exchange_api import (
    SignalExchangeAPIWithSimpleUpdates,
)
from threatexchange.exchanges.collab_config import CollaborationConfigWithDefaults
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.exchanges.impl.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)

_API_NAME = "fb_threatexchange"


@dataclass
class _FBThreatExchangeCollabConfigRequiredFields:
    privacy_group: int = field(
        metadata={
            "help": "ThreatPrivacyGroup ID for this collaboration",
            "metavar": "id",
        }
    )


@dataclass
class FBThreatExchangeCollabConfig(
    CollaborationConfigWithDefaults,
    _FBThreatExchangeCollabConfigRequiredFields,
):
    api: str = field(init=False, default=_API_NAME)
    # TODO - to restore someday in the future
    # app_token_override: t.Optional[str] = field(
    #     default=None,
    #     metadata={
    #         "help": "if you need to use a specific app for this collaboration",
    #         "metavar": "APP_TOKEN",
    #     },
    # )


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

    owner_app_id: int
    descriptor_id: t.Optional[int]

    def __setstate__(self, d: t.Dict[str, t.Any]) -> None:
        """Implemented for pickle version compatibility."""
        # 0.99.0 => 1.0.0:
        ### field 'owner_id' renamed to 'owner_app_id' and 'is_mine'
        if "owner" in d:
            d["owner_app_id"] = d["owner"]
        super().__setstate__(d)


@dataclass
class FBThreatExchangeIndicatorRecord(state.FetchedSignalMetadata):

    opinions: t.List[FBThreatExchangeOpinion]

    def get_as_opinions(
        self,
    ) -> t.List[FBThreatExchangeOpinion]:
        return self.opinions

    @classmethod
    def from_threatexchange_json(
        cls, my_app_id: int, te_json: ThreatUpdateJSON
    ) -> t.Optional["FBThreatExchangeIndicatorRecord"]:
        if te_json.should_delete:
            return None

        explicit_opinions: t.Dict[int, FBThreatExchangeOpinion] = {}
        implicit_opinions: t.Dict[int, state.SignalOpinionCategory] = {}

        for td_json in te_json.raw_json["descriptors"]["data"]:
            td_id = int(td_json["id"])
            owner_id = int(td_json["owner"]["id"])
            status = td_json["status"]
            # added_on = td_json["added_on"]
            tags = td_json.get("tags", [])
            # This is needed because ThreatExchangeAPI.get_threat_descriptors()
            # does a transform, but other locations do not
            if isinstance(tags, dict):
                tags = sorted(tag["text"] for tag in tags["data"])

            category = state.SignalOpinionCategory.INVESTIGATION_SEED

            if status == "MALICIOUS":
                category = state.SignalOpinionCategory.POSITIVE_CLASS
            elif status == "NON_MALICIOUS":
                category = state.SignalOpinionCategory.NEGATIVE_CLASS

            explicit_opinions[owner_id] = FBThreatExchangeOpinion(
                owner_id == my_app_id,
                category,
                set(tags),
                owner_id,
                td_id,
            )

            # See: https://developers.facebook.com/docs/threat-exchange/reference/apis/reaction-type/
            for reaction in td_json.get("reactions", []):
                rxn = reaction["key"]
                for owner in reaction["value"].split(","):
                    owner_id = int(owner)
                    if rxn == "HELPFUL":
                        implicit_opinions[
                            owner_id
                        ] = state.SignalOpinionCategory.POSITIVE_CLASS
                    elif (
                        rxn == "DISAGREE_WITH_TAGS"
                        and owner_id not in implicit_opinions
                    ):
                        implicit_opinions[
                            owner_id
                        ] = state.SignalOpinionCategory.NEGATIVE_CLASS

        for owner_id, category in implicit_opinions.items():
            if owner_id in explicit_opinions:
                continue
            explicit_opinions[owner_id] = FBThreatExchangeOpinion(
                owner_id == my_app_id,
                category,
                set(),
                owner_id,
                FBThreatExchangeOpinion.REACTION_DESCRIPTOR_ID,
            )

        if not explicit_opinions:
            # Visibility bug of some kind on TE API :(
            return None
        return cls(list(explicit_opinions.values()))

    def merge(self, other: "FBThreatExchangeIndicatorRecord") -> None:
        """
        Combine another indicator record with this one.

        This is needed when there are multiple records in ThreatExchange
        of equivalent types - i.e.
          * URI
          * RAW_URI
          * UNCLICKABLE_URL

        Most of the time, platforms record the exact same record for each,
        but it's not guaranteed.
        """
        # We could try to dedupe identical opinions, but instead just take
        # them all
        self.opinions.extend(other.opinions)

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


@dataclass
class FBThreatExchangeCredentials(auth.CredentialHelper):
    ENV_VARIABLE: t.ClassVar[str] = "TX_ACCESS_TOKEN"
    FILE_NAME: t.ClassVar[str] = "~/.txtoken"

    api_token: str

    @classmethod
    def _from_str(cls, s: str) -> t.Optional["FBThreatExchangeCredentials"]:
        return cls(s.strip())

    def _are_valid(self) -> bool:
        return is_valid_app_token(self.api_token)


ThreatExchangeDelta = state.FetchDelta[
    t.Tuple[str, str],
    FBThreatExchangeIndicatorRecord,
    FBThreatExchangeCheckpoint,
]


class FBThreatExchangeSignalExchangeAPI(
    auth.SignalExchangeWithAuth[
        FBThreatExchangeCollabConfig, FBThreatExchangeCredentials
    ],
    SignalExchangeAPIWithSimpleUpdates[
        FBThreatExchangeCollabConfig,
        FBThreatExchangeCheckpoint,
        FBThreatExchangeIndicatorRecord,
    ],
):
    def __init__(
        self, client: ThreatExchangeAPI, collab: FBThreatExchangeCollabConfig
    ) -> None:
        self.client = client
        self.collab = collab

    @classmethod
    def for_collab(
        cls,
        collab: FBThreatExchangeCollabConfig,
        credentials: t.Optional[FBThreatExchangeCredentials] = None,
    ) -> "FBThreatExchangeSignalExchangeAPI":
        credentials = credentials or FBThreatExchangeCredentials.get(cls)
        client = ThreatExchangeAPI(credentials.api_token)
        return cls(client, collab)

    @classmethod
    def get_name(cls) -> str:
        return _API_NAME

    @staticmethod
    def get_checkpoint_cls() -> t.Type[FBThreatExchangeCheckpoint]:
        return FBThreatExchangeCheckpoint

    @staticmethod
    def get_record_cls() -> t.Type[FBThreatExchangeIndicatorRecord]:
        return FBThreatExchangeIndicatorRecord

    @staticmethod
    def get_config_cls() -> t.Type[FBThreatExchangeCollabConfig]:
        return FBThreatExchangeCollabConfig

    @staticmethod
    def get_credential_cls() -> t.Type[FBThreatExchangeCredentials]:
        return FBThreatExchangeCredentials

    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[FBThreatExchangeCheckpoint],
    ) -> t.Iterator[ThreatExchangeDelta]:
        start_time = None if checkpoint is None else checkpoint.update_time
        cursor = self.client.get_threat_updates(
            self.collab.privacy_group,
            start_time=start_time,
            page_size=100,
            fields=ThreatUpdateJSON.te_threat_updates_fields(),
            decode_fn=ThreatUpdateJSON,
        )
        type_mapping = _make_indicator_type_mapping(supported_signal_types)

        highest_time = start_time or 0
        batch: t.List[ThreatUpdateJSON]
        for batch in cursor:
            assert batch, "empty update?"
            highest_time = max(highest_time, max(update.time for update in batch))

            updates = {}
            for u in batch:
                updates[u.threat_type, u.indicator] = _indicator_applies(
                    self.client.app_id, u, type_mapping
                )

            yield ThreatExchangeDelta(
                updates,
                FBThreatExchangeCheckpoint(highest_time),
            )

    @classmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        collab: FBThreatExchangeCollabConfig,
        fetched: t.Mapping[
            t.Tuple[str, str], t.Optional[FBThreatExchangeIndicatorRecord]
        ],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, FBThreatExchangeIndicatorRecord]]:
        """
        Convert ThreatExchange Indicator records to SignalTypes.

        We override this method from the base in order to make the signal type
        mapping just once.

        ThreatExchange uses a helper mixin that SignalTypes can implement in order
        to instruct the API how to convert ThreatExchange's ThreatType into
        a SignalType. ThreatExchange supports multiple ThreatTypes for the same
        SignalType, and so it's possible there are duplicate records. It's even
        possible that the uploader isn't consistent with their labeling for the
        "identical" records in ThreatExchange.
        """
        ret: t.Dict[
            t.Type[SignalType], t.Dict[str, FBThreatExchangeIndicatorRecord]
        ] = {}
        mapping = _make_indicator_type_mapping(signal_types)

        for (type_str, signal_str), metadata in fetched.items():
            potential_types = mapping.get(type_str)
            if potential_types is None or metadata is None:
                continue
            indicator_tags = {t for opinion in metadata.opinions for t in opinion.tags}
            for tag, s_types in potential_types.items():
                if tag is not None and tag not in indicator_tags:
                    continue
                for tx_s_type in s_types:
                    s_type_specific_signal_str = (
                        tx_s_type.normalize_fb_threatexchange_indicator(
                            type_str, signal_str, tag
                        )
                    )
                    s_type = t.cast(t.Type[SignalType], tx_s_type)
                    inner = ret.get(s_type)
                    if inner is None:
                        inner = {}
                        ret[s_type] = inner
                    to_insert = _merge_record_for_signal_type(
                        metadata, tag, inner.get(s_type_specific_signal_str)
                    )
                    if to_insert is not None:
                        inner[s_type_specific_signal_str] = to_insert

        return ret


def _merge_record_for_signal_type(
    tx_record: FBThreatExchangeIndicatorRecord,
    tag: t.Optional[str],
    existing: t.Optional[FBThreatExchangeIndicatorRecord],
) -> t.Optional[FBThreatExchangeIndicatorRecord]:
    if tag is not None:
        applicable_opinions = [
            o for o in tx_record.opinions if any(t in tag for t in o.tags)
        ]
        if not applicable_opinions:
            return None
        if len(applicable_opinions) != len(tx_record.opinions):
            tx_record = FBThreatExchangeIndicatorRecord(applicable_opinions)
    if existing is not None:
        existing.merge(tx_record)
        return None
    return tx_record


def _indicator_applies(
    my_app_id: int,
    u: ThreatUpdateJSON,
    type_mapping: t.Mapping[
        str,
        t.Mapping[
            t.Optional[str], t.Sequence[t.Type[HasFbThreatExchangeIndicatorType]]
        ],
    ],
) -> t.Optional[FBThreatExchangeIndicatorRecord]:
    """Based on the available signal types, return a record"""
    potential_signal_type = type_mapping.get(u.threat_type)
    if potential_signal_type is None:
        return None
    indicator = FBThreatExchangeIndicatorRecord.from_threatexchange_json(my_app_id, u)
    if indicator is None:
        return None
    if None in potential_signal_type:
        return indicator
    if any(
        tag in potential_signal_type
        for opinion in indicator.opinions
        for tag in opinion.tags
    ):
        return indicator
    return None


def _make_indicator_type_mapping(
    supported_signal_types: t.Sequence[t.Type[SignalType]],
) -> t.Mapping[
    str,
    t.Mapping[t.Optional[str], t.Sequence[t.Type[HasFbThreatExchangeIndicatorType]]],
]:
    """
    Based on the given signal types, create a map for converting ThreatIndicators.

    The returned mapping is ThreatType => ?tag => SignalType.

    For example, with MD5, and one test type:
    ```
    {
       "HASH_VIDEO_MD5": {
           None: [VideoMd5Signal],
        },
        "HASH_MD5": {
           "media_type_video": [VideoMD5Signal]
        }
        "DEBUG_STRING": {
            "type:foo": [FooType],
        }
    }
    ```
    """
    ret: t.DefaultDict[
        str,
        t.DefaultDict[
            t.Optional[str], t.List[t.Type[HasFbThreatExchangeIndicatorType]]
        ],
    ] = defaultdict(lambda: defaultdict(list))
    for st in supported_signal_types:
        if not issubclass(st, HasFbThreatExchangeIndicatorType):
            continue
        types = st.INDICATOR_TYPE
        if isinstance(types, str):
            types = {types: None}
        elif isinstance(types, set):
            types = {tag: None for tag in types}
        else:
            assert isinstance(types, dict)
        for type_, tag in types.items():
            ret[type_][tag].append(st)

    return ret
