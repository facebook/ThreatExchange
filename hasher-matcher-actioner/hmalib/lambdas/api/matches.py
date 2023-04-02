# Copyright (c) Meta Platforms, Inc. and affiliates.

import boto3
import bottle
import functools
import dataclasses

from dataclasses import dataclass, asdict
from mypy_boto3_dynamodb.service_resource import Table
import typing as t
from enum import Enum
from urllib.error import HTTPError
from mypy_boto3_sqs.client import SQSClient

from threatexchange.exchanges.clients.fb_threatexchange.descriptor import (
    ThreatDescriptor,
)
from threatexchange.signal_type.index import IndexMatch
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.interface_validation import FunctionalityMapping, SignalTypeMapping

from hmalib.common.models.pipeline import MatchRecord
from hmalib.common.models.signal import (
    ThreatExchangeSignalMetadata,
    PendingThreatExchangeOpinionChange,
)
from hmalib.common.logging import get_logger
from hmalib.common.mappings import HMASignalTypeMapping
from hmalib.common.messages.match import BankedSignal
from hmalib.common.messages.writeback import WritebackMessage
from hmalib.indexers.metadata import (
    BANKS_SOURCE_SHORT_CODE,
    BankedSignalIndexMetadata,
)
from hmalib.lambdas.api.middleware import (
    DictParseableWithSignalTypeMapping,
    jsoninator,
    JSONifiable,
    DictParseable,
    SubApp,
)
from hmalib.common.config import HMAConfig
from hmalib.common.models.bank import BankMember, BanksTable
from hmalib.matchers.matchers_base import Matcher

from hmalib.hashing.unified_hasher import UnifiedHasher
from hmalib.common.content_sources import URLContentSource


logger = get_logger(__name__)


@functools.lru_cache(maxsize=None)
def _get_sqs_client() -> SQSClient:
    return boto3.client("sqs")


_matcher = None


def _get_matcher(index_bucket_name: str, banks_table: BanksTable) -> Matcher:
    global _matcher
    if _matcher is None:
        _matcher = Matcher(
            index_bucket_name=index_bucket_name,
            supported_signal_types=[PdqSignal, VideoMD5Signal],
            banks_table=banks_table,
        )

    return _matcher


_hasher = None


def _get_hasher(signal_type_mapping: HMASignalTypeMapping) -> UnifiedHasher:
    global _hasher
    if _hasher is None:
        _hasher = UnifiedHasher(
            signal_type_mapping=signal_type_mapping,
            output_queue_url="",
        )

    return _hasher


@dataclass
class MatchSummary(JSONifiable):
    content_id: str
    signal_id: t.Union[str, int]
    signal_source: str
    updated_at: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class MatchSummariesResponse(JSONifiable):
    match_summaries: t.List[MatchSummary]

    def to_json(self) -> t.Dict:
        return {
            "match_summaries": [summary.to_json() for summary in self.match_summaries]
        }


@dataclass
class BankedSignalDetailsMetadata(JSONifiable):
    bank_member_id: str
    bank_id: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class ThreatExchangeSignalDetailsMetadata(JSONifiable):
    privacy_group_id: str
    tags: t.List[str]
    opinion: str
    pending_opinion_change: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class MatchDetail(JSONifiable):
    """
    Note: te_signal_details should eventaully be folded into banked_signal_details
    once threatexchanges signals function the same as locally banked one.
    """

    content_id: str
    content_hash: str
    signal_id: t.Union[str, int]
    signal_hash: str
    signal_source: str
    signal_type: str
    updated_at: str
    match_distance: t.Optional[int]
    te_signal_details: t.List[ThreatExchangeSignalDetailsMetadata]
    banked_signal_details: t.List[BankedSignalDetailsMetadata]

    def to_json(self) -> t.Dict:
        result = asdict(self)
        result.update(
            te_signal_details=[datum.to_json() for datum in self.te_signal_details]
        )
        result.update(
            banked_signal_details=[
                datum.to_json() for datum in self.banked_signal_details
            ]
        )
        return result


@dataclass
class MatchDetailsResponse(JSONifiable):
    match_details: t.List[MatchDetail]

    def to_json(self) -> t.Dict:
        return {"match_details": [detail.to_json() for detail in self.match_details]}


@dataclass
class ChangeSignalOpinionResponse(JSONifiable):
    success: bool

    def to_json(self) -> t.Dict:
        return {"change_requested": self.success}


def get_match_details(
    datastore_table: Table,
    banks_table: BanksTable,
    content_id: str,
    signal_type_mapping: HMASignalTypeMapping,
) -> t.List[MatchDetail]:
    if not content_id:
        return []

    records = MatchRecord.get_from_content_id(
        datastore_table, f"{content_id}", signal_type_mapping
    )

    return [
        MatchDetail(
            content_id=record.content_id,
            content_hash=record.content_hash,
            signal_id=record.signal_id,
            signal_hash=record.signal_hash,
            signal_source=record.signal_source,
            signal_type=record.signal_type.get_name(),
            updated_at=record.updated_at.isoformat(),
            match_distance=int(record.match_distance)
            if record.match_distance is not None
            else None,
            te_signal_details=get_te_signal_details(
                datastore_table=datastore_table,
                signal_id=record.signal_id,
                signal_source=record.signal_source,
                signal_type_mapping=signal_type_mapping,
            ),
            banked_signal_details=get_banked_signal_details(
                banks_table=banks_table,
                signal_id=record.signal_id,
                signal_source=record.signal_source,
            ),
        )
        for record in records
    ]


def get_te_signal_details(
    datastore_table: Table,
    signal_id: str,
    signal_source: str,
    signal_type_mapping: SignalTypeMapping,
) -> t.List[ThreatExchangeSignalDetailsMetadata]:
    """
    Note: te_signal_details should eventaully be folded into banked_signal_details
    once threatexchanges signals function the same as locally banked one.
    """
    if not signal_id or not signal_source or signal_source == BANKS_SOURCE_SHORT_CODE:
        return []

    return [
        ThreatExchangeSignalDetailsMetadata(
            privacy_group_id=metadata.privacy_group_id,
            tags=[
                tag for tag in metadata.tags if tag not in ThreatDescriptor.SPECIAL_TAGS
            ],
            opinion=get_opinion_from_tags(metadata.tags).value,
            pending_opinion_change=metadata.pending_opinion_change.value,
        )
        for metadata in ThreatExchangeSignalMetadata.get_from_signal(
            datastore_table, signal_id, signal_type_mapping
        )
    ]


def get_banked_signal_details(
    banks_table: BanksTable,
    signal_id: str,
    signal_source: str,
) -> t.List[BankedSignalDetailsMetadata]:
    if not signal_id or not signal_source or signal_source != BANKS_SOURCE_SHORT_CODE:
        return []

    return [
        BankedSignalDetailsMetadata(
            bank_member_id=bank_member_signal.bank_member_id,
            bank_id=bank_member_signal.bank_id,
        )
        for bank_member_signal in banks_table.get_bank_member_signal_from_id(signal_id)
    ]


class OpinionString(Enum):
    TRUE_POSITIVE = "True Positive"
    FALSE_POSITIVE = "False Positive"
    DISPUTED = "Disputed"
    UNKNOWN = "Unknown"


def get_opinion_from_tags(tags: t.List[str]) -> OpinionString:
    # see python-threatexchange descriptor.py for origins
    if ThreatDescriptor.TRUE_POSITIVE in tags:
        return OpinionString.TRUE_POSITIVE
    if ThreatDescriptor.FALSE_POSITIVE in tags:
        return OpinionString.FALSE_POSITIVE
    if ThreatDescriptor.DISPUTED in tags:
        return OpinionString.DISPUTED
    return OpinionString.UNKNOWN


@dataclass
class MatchesForHashRequest(DictParseableWithSignalTypeMapping):
    signal_value: str
    signal_type: t.Type[SignalType]

    @classmethod
    def from_dict(
        cls, d: t.Dict, signal_type_mapping: HMASignalTypeMapping
    ) -> "MatchesForHashRequest":
        base = cls(**{f.name: d.get(f.name, None) for f in dataclasses.fields(cls)})
        base.signal_type = signal_type_mapping.get_signal_type_enforce(
            t.cast(str, base.signal_type)
        )
        return t.cast("MatchesForHashRequest", base)


@dataclass
class MatchesForMediaRequest(DictParseableWithSignalTypeMapping):
    content_url: str
    content_type: t.Type[ContentType]

    @classmethod
    def from_dict(cls, d, signal_type_mapping: HMASignalTypeMapping):
        base = cls(**{f.name: d.get(f.name, None) for f in dataclasses.fields(cls)})
        base.content_type = signal_type_mapping.get_content_type_enforce(
            t.cast(str, base.content_type)
        )
        return t.cast("MatchesForMediaRequest", base)


@dataclass
class MatchesForHash(JSONifiable):
    match_distance: int

    # TODO: Once ThreatExchange data flows into Banks, we can Use BankMember
    # alone.
    matched_signal: t.Union[
        ThreatExchangeSignalMetadata, BankMember
    ]  # or matches signal from other sources

    UNSUPPORTED_FIELDS = ["updated_at", "pending_opinion_change"]

    def to_json(self) -> t.Dict:
        return {
            "match_distance": self.match_distance,
            "matched_signal": self._remove_unsupported_fields(
                self.matched_signal.to_json()
            ),
        }

    @classmethod
    def _remove_unsupported_fields(cls, matched_signal: t.Dict) -> t.Dict:
        """
        ThreatExchangeSignalMetadata is used to store metadata in dynamodb
        and handle opinion changes on said signal. However the request this object
        responds to only handles directly accessing the index. Because of this
        not all fields of the object are relevant or accurate.
        """
        for field in cls.UNSUPPORTED_FIELDS:
            try:
                del matched_signal[field]
            except KeyError:
                pass
        return matched_signal


@dataclass
class MatchesForHashResponse(JSONifiable):
    matches: t.List[MatchesForHash]

    def to_json(self) -> t.Dict:
        return {"matches": [match.to_json() for match in self.matches]}


@dataclass
class MatchesForMediaResponse(JSONifiable):
    signal_to_matches: t.Dict[str, t.Dict[str, t.List[MatchesForHash]]]
    # example: { "pdq" : { "<hash>" : [<matches?>] } }

    def to_json(self) -> t.Dict:
        return {
            "signal_to_matches": {
                signal_type: {signal_val: [match.to_json() for match in matches]}
                for (signal_val, matches) in hash_to_match.items()
            }
            for (signal_type, hash_to_match) in self.signal_to_matches.items()
        }


@dataclass
class MediaFetchError(JSONifiable):
    def to_json(self) -> t.Dict:
        return {
            "message": "Failed to fetch media from provided url",
        }


def get_matches_api(
    datastore_table: Table,
    hma_config_table: str,
    indexes_bucket_name: str,
    writeback_queue_url: str,
    bank_table: Table,
    signal_type_mapping: HMASignalTypeMapping,
) -> bottle.Bottle:
    """
    A Closure that includes all dependencies that MUST be provided by the root
    API that this API plugs into. Declare dependencies here, but initialize in
    the root API alone.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/matches/'
    matches_api = SubApp()
    HMAConfig.initialize(hma_config_table)

    banks_table = BanksTable(table=bank_table, signal_type_mapping=signal_type_mapping)

    @matches_api.get("/", apply=[jsoninator])
    def matches() -> MatchSummariesResponse:
        """
        Return all, or a filtered list of matches based on query params.
        """
        signal_q = bottle.request.query.signal_q or None  # type: ignore # ToDo refactor to use `jsoninator(<requestObj>, from_query=True)``
        signal_source = bottle.request.query.signal_source or None  # type: ignore # ToDo refactor to use `jsoninator(<requestObj>, from_query=True)``
        content_q = bottle.request.query.content_q or None  # type: ignore # ToDo refactor to use `jsoninator(<requestObj>, from_query=True)``

        if content_q:
            records = MatchRecord.get_from_content_id(
                datastore_table, content_q, signal_type_mapping
            )
        elif signal_q:
            records = MatchRecord.get_from_signal(
                datastore_table, signal_q, signal_source or "", signal_type_mapping
            )
        else:
            # TODO: Support pagination after implementing in UI.
            records = MatchRecord.get_recent_items_page(
                datastore_table, signal_type_mapping
            ).items

        return MatchSummariesResponse(
            match_summaries=[
                MatchSummary(
                    content_id=record.content_id,
                    signal_id=record.signal_id,
                    signal_source=record.signal_source,
                    updated_at=record.updated_at.isoformat(),
                )
                for record in records
            ]
        )

    @matches_api.get("/match/", apply=[jsoninator])
    def match_details() -> MatchDetailsResponse:
        """
        Return the match details for a given content id.
        """
        results = []
        if content_id := bottle.request.query.content_id or None:  # type: ignore # ToDo refactor to use `jsoninator(<requestObj>, from_query=True)``
            results = get_match_details(
                datastore_table=datastore_table,
                banks_table=banks_table,
                content_id=content_id,
                signal_type_mapping=signal_type_mapping,
            )
        return MatchDetailsResponse(match_details=results)

    @matches_api.post("/request-signal-opinion-change/", apply=[jsoninator])
    def request_signal_opinion_change() -> ChangeSignalOpinionResponse:
        """
        Request a change to the opinion for a signal in a given privacy_group.
        """
        signal_id = bottle.request.query.signal_id or None  # type: ignore # ToDo refactor to use `jsoninator(<requestObj>, from_query=True)``
        signal_source = bottle.request.query.signal_source or None  # type: ignore # ToDo refactor to use `jsoninator(<requestObj>, from_query=True)``
        privacy_group_id = bottle.request.query.privacy_group_id or None  # type: ignore # ToDo refactor to use `jsoninator(<requestObj>, from_query=True)``
        opinion_change = bottle.request.query.opinion_change or None  # type: ignore # ToDo refactor to use `jsoninator(<requestObj>, from_query=True)``

        if (
            not signal_id
            or not signal_source
            or not privacy_group_id
            or not opinion_change
        ):
            return ChangeSignalOpinionResponse(False)

        signal_id = str(signal_id)
        pending_opinion_change = PendingThreatExchangeOpinionChange(opinion_change)

        writeback_message = WritebackMessage.from_banked_signal_and_opinion_change(
            BankedSignal(signal_id, privacy_group_id, signal_source),
            pending_opinion_change,
        )
        writeback_message.send_to_queue(_get_sqs_client(), writeback_queue_url)
        logger.info(
            f"Opinion change enqueued for {signal_source}:{signal_id} in {privacy_group_id} change={opinion_change}"
        )

        signal = ThreatExchangeSignalMetadata.get_from_signal_and_privacy_group(
            datastore_table,
            signal_id=signal_id,
            privacy_group_id=privacy_group_id,
            signal_type_mapping=signal_type_mapping,
        )

        if not signal:
            logger.error("Signal not found.")

        signal = t.cast(ThreatExchangeSignalMetadata, signal)
        signal.pending_opinion_change = pending_opinion_change
        success = signal.update_pending_opinion_change_in_table_if_exists(
            datastore_table
        )

        if not success:
            logger.error(f"Attempting to update {signal} in db failed")

        return ChangeSignalOpinionResponse(success)

    def _matches_for_hash(
        signal_type: t.Type[SignalType], signal_value: str
    ) -> t.List[MatchesForHash]:
        matches = _get_matcher(indexes_bucket_name, banks_table=banks_table).match(
            signal_type, signal_value
        )

        match_objects: t.List[MatchesForHash] = []

        # First get all threatexchange objects
        for match in matches:
            match_objects.extend(
                [
                    MatchesForHash(
                        match_distance=_distance_from_match_if_exits(match),
                        matched_signal=signal_metadata,
                    )
                    for signal_metadata in Matcher.get_te_metadata_objects_from_match(
                        signal_type, match
                    )
                ]
            )

        # now get all bank objects
        for match in matches:
            for metadata_obj in filter(
                lambda m: m.get_source() == BANKS_SOURCE_SHORT_CODE, match.metadata
            ):
                metadata_obj = t.cast(BankedSignalIndexMetadata, metadata_obj)
                match_objects.append(
                    MatchesForHash(
                        match_distance=_distance_from_match_if_exits(match),
                        matched_signal=banks_table.get_bank_member(
                            metadata_obj.bank_member_id
                        ),
                    )
                )

        return match_objects

    def _distance_from_match_if_exits(match: IndexMatch) -> int:
        """
        Existing API expects an int, the newer SignalType interface is
        not as specific.
        TODO update the API to return a string for distance so support
        various differences.
        """
        if hasattr(match.similarity_info, "distance") and isinstance(
            match.similarity_info.distance, int
        ):
            return int(match.similarity_info.distance)
        return 0

    @matches_api.get(
        "/for-hash/",
        apply=[
            jsoninator(
                MatchesForHashRequest,
                from_query=True,
                signal_type_mapping=signal_type_mapping,
            )
        ],
    )
    def for_hash(request: MatchesForHashRequest) -> MatchesForHashResponse:
        """
        For a given hash/signal check the index(es) for matches and return the details.

        This does not change system state, metadata returned will not be written any tables
        unlike when matches are found for submissions.
        """

        return MatchesForHashResponse(
            matches=_matches_for_hash(request.signal_type, request.signal_value)
        )

    @matches_api.post(
        "/for-media/",
        apply=[
            jsoninator(MatchesForMediaRequest, signal_type_mapping=signal_type_mapping)
        ],
    )
    def for_media(
        request: MatchesForMediaRequest,
    ) -> t.Union[MatchesForMediaResponse, MediaFetchError]:
        """
        For a given piece of media hash it, check the index(es) for matches, and return the details.

        This does not change system state, metadata returned will not be written any tables
        unlike when matches are found for submissions.
        """
        try:
            bytes_: bytes = URLContentSource().get_bytes(request.content_url)
        except Exception as e:
            bottle.response.status = 400
            return MediaFetchError()

        signal_to_matches = {}
        for signal in _get_hasher(signal_type_mapping=signal_type_mapping).get_hashes(
            request.content_type, bytes_
        ):
            signal_to_matches[signal.signal_type.get_name()] = {
                signal.signal_value: _matches_for_hash(
                    signal_type=signal.signal_type, signal_value=signal.signal_value
                )
            }

        return MatchesForMediaResponse(signal_to_matches=signal_to_matches)

    return matches_api
