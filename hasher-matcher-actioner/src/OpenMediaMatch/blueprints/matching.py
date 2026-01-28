# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Endpoints for matching content and hashes.
"""

from dataclasses import dataclass
import datetime
import random
import typing as t
import time

from flask_openapi3 import APIBlueprint
from flask_openapi3.models import Tag
from flask import Flask, Response, abort, current_app, request
from werkzeug.datastructures import Headers

# Needed so typing.get_type_hints resolves ResponseReturnValue's WSGIApplication during tests.
WSGIApplication = t.Callable[..., t.Any]
from flask.typing import ResponseReturnValue
from flask_apscheduler import APScheduler
from werkzeug.exceptions import HTTPException

from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.index import (
    IndexMatchUntyped,
    SignalSimilarityInfo,
    SignalTypeIndex,
)

from OpenMediaMatch.background_tasks.development import get_apscheduler
from OpenMediaMatch.storage import interface
from OpenMediaMatch.blueprints import hashing
from OpenMediaMatch.utils.flask_utils import (
    api_error_handler,
)
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.utils.memory_utils import trim_process_memory
from OpenMediaMatch.schemas.matching import (
    CompareRequest,
    CompareResponse,
    IndexStatusResponse,
    LookupRequest,
    LookupResponse,
    MatchWithDistance as MatchWithDistanceModel,
    RawLookupRequest,
    RawLookupResponse,
)
from OpenMediaMatch.schemas.shared import ErrorResponse

bp = APIBlueprint("matching", __name__, url_prefix="/m")
bp.register_error_handler(HTTPException, api_error_handler)


# Type helpers


class MatchWithDistancePayload(t.TypedDict):
    bank_content_id: int
    distance: str


TMatchByBank = dict[str, list[MatchWithDistancePayload]]
TBankMatchBySignalType = dict[str, TMatchByBank]


@dataclass
class _SignalIndexInMemoryCache:
    signal_type: t.Type[SignalType]
    index: SignalTypeIndex[int]
    checkpoint: interface.SignalTypeIndexBuildCheckpoint
    last_check_ts: float
    sec_old_before_stale: int

    @property
    def is_ready(self):
        return self.last_check_ts > 0

    @property
    def is_stale(self):
        """
        If we are overdue on refresh by too long, consider it stale.
        """
        limit = self.sec_old_before_stale
        if limit <= 0:  # 0 disables stale check
            return False
        return time.time() - self.last_check_ts > limit

    @classmethod
    def get_initial(
        cls, signal_type: t.Type[SignalType], sec_old_before_stale: int
    ) -> t.Self:
        return cls(
            signal_type,
            signal_type.get_index_cls().build([]),
            interface.SignalTypeIndexBuildCheckpoint.get_empty(),
            0,
            sec_old_before_stale,
        )

    def reload_if_needed(self, store: interface.IUnifiedStore) -> None:
        now = time.time()
        # There's a race condition here, but it's unclear if we should solve it
        curr_checkpoint = store.get_last_index_build_checkpoint(self.signal_type)
        if curr_checkpoint is not None and self.checkpoint != curr_checkpoint:
            new_index = store.get_signal_type_index(self.signal_type)
            if new_index is None:
                app: Flask = get_apscheduler().app
                app.logger.error(
                    "CachedIndex[%s] index checkpoint(%r)"
                    + " says new index available but unable to get it",
                    self.signal_type.get_name(),
                    curr_checkpoint,
                )
                return

            self.index = new_index
            self.checkpoint = curr_checkpoint

            # Force garbage collection to reclaim memory and attempt to free pages
            trim_process_memory()

        self.last_check_ts = now

    def periodic_task(self) -> None:
        app: Flask = get_apscheduler().app
        with app.app_context():
            storage = get_storage()
            prev_time = self.checkpoint.last_item_timestamp
            self.reload_if_needed(storage)
            now_time = self.checkpoint.last_item_timestamp
            if prev_time == now_time:
                return  # No reload
            app.logger.info(
                "CachedIndex[%s] Updated %d -> %d",
                self.signal_type.get_name(),
                prev_time,
                now_time,
            )


# This is a type alias, the actual cache is stored on app
IndexCache = t.Mapping[str, _SignalIndexInMemoryCache]


@bp.get(
    "/raw_lookup",
    tags=[Tag(name="Matching")],
    responses={"200": RawLookupResponse, "400": ErrorResponse, "503": ErrorResponse},
    summary="Raw hash lookup",
    description="Look up a hash in the similarity index",
)
def raw_lookup(query: RawLookupRequest) -> ResponseReturnValue:
    """
    Look up a hash in the similarity index.

    Note that enable/disable status is NOT checked - you'll need to do it
    yourself or call /lookup instead.

    Input:
     * Signal type (hash type)
     * Signal value (the hash)
     * Optional list of banks to restrict search to
     * Optional include_distance (bool) whether or not to return distance values on match
    Output:
     * List of matching with content_id and, if included, distance values
    """
    # Parse optional banks parameter
    requested_banks = set(query.banks.split(",")) if query.banks else None

    lookup_signal_func = (
        lookup_signal_with_distance if query.include_distance else lookup_signal
    )

    matches = lookup_signal_func(query.signal, query.signal_type, requested_banks)

    if query.include_distance:
        distance_matches = t.cast(list[MatchWithDistancePayload], matches)
        response = RawLookupResponse(
            matches=[MatchWithDistanceModel(**match) for match in distance_matches]
        )
        return response.model_dump()

    matches_union: list[int | MatchWithDistanceModel] = [
        t.cast(int | MatchWithDistanceModel, match) for match in matches
    ]
    return RawLookupResponse(matches=matches_union).model_dump()


def query_index(
    signal: str, signal_type_name: str
) -> t.Sequence[IndexMatchUntyped[SignalSimilarityInfo, int]]:
    storage = get_storage()
    signal_type = _validate_and_transform_signal_type(signal_type_name, storage)

    try:
        signal = signal_type.validate_signal_str(signal)
    except Exception as e:
        abort(400, f"invalid signal: {e}")

    index = _get_index(signal_type)

    if index is None:
        abort(503, "index not yet ready")
    current_app.logger.debug("[lookup_signal] querying index")
    results = index.query(signal)
    current_app.logger.debug("[lookup_signal] query complete")
    return results


def lookup_signal(
    signal: str, signal_type_name: str, banks: t.Optional[t.Set[str]] = None
) -> list[int]:
    results = query_index(signal, signal_type_name)
    content_ids = [m.metadata for m in results]

    # Filter by banks if specified
    if banks is not None:
        storage = get_storage()
        contents = storage.bank_content_get(content_ids)
        content_ids = [c.id for c in contents if c.bank.name in banks]

    return content_ids


def lookup_signal_with_distance(
    signal: str, signal_type_name: str, banks: t.Optional[t.Set[str]] = None
) -> list[MatchWithDistancePayload]:
    results = query_index(signal, signal_type_name)
    matches: list[MatchWithDistancePayload] = [
        {
            "bank_content_id": m.metadata,
            "distance": m.similarity_info.pretty_str(),
        }
        for m in results
    ]

    # Filter by banks if specified
    if banks is not None:
        storage = get_storage()
        content_ids = [m["bank_content_id"] for m in matches]
        contents = storage.bank_content_get(content_ids)
        # Create a set of valid content IDs
        valid_content_ids = {c.id for c in contents if c.bank.name in banks}
        # Filter matches to only include valid content IDs
        matches = [m for m in matches if m["bank_content_id"] in valid_content_ids]

    return matches


def _validate_and_transform_signal_type(
    signal_type_name: str, storage: interface.ISignalTypeConfigStore
) -> type[SignalType]:
    """
    Accepts a signal type name and returns the corresponding signal type class,
    validating that the signal type exists and is enabled for the provided storage.
    """
    signal_type_config = storage.get_signal_type_configs().get(signal_type_name)
    if signal_type_config is None:
        abort(400, f"No such SignalType '{signal_type_name}'")
    if not signal_type_config.enabled:
        abort(400, f"SignalType '{signal_type_name}' is not enabled")
    return signal_type_config.signal_type


@bp.get(
    "/lookup",
    tags=[Tag(name="Matching")],
    responses={"200": LookupResponse, "400": ErrorResponse, "403": ErrorResponse},
    summary="Content lookup",
    description="Look up content by URL or hash in the similarity index",
)
def lookup_get(query: LookupRequest) -> ResponseReturnValue:
    """
    Look up a hash in the similarity index. The hash can either be specified via
    `signal_type` and `signal` query params, or a file url can be provided in the
    `url` query param.
    Input:
     Either:
     * File URL (`url`)
     * Optional content type (`content_type`)
     Or:
     * Signal type (hash type)
     * Signal value (the hash)

     Also (applies to both cases):
     * Optional seed (content id) for consistent coinflip
    Output:
     * JSON object keyed by signal type, to a JSON object of bank
       matches. If Signal Type is given, the outer JSON object is
       elided.

    Example output:
    {
        "pdq": {
            "BANK_A": [
                {"bank_content_id": 1001, "distance": 4},
                {"bank_content_id": 1002, "distance": 0},
            ],
            "BANK_B": [
                {"bank_content_id": 4434, "distance": 0},
            ]
        },
    }

    Example output (with signal type set)
    {
        "BANK_A": [
            {"bank_content_id": 1001, "distance": 4},
            {"bank_content_id": 1002, "distance": 0},
        ],
        "BANK_B": [
            {"bank_content_id": 4434, "distance": 0},
        ]
    }
    """
    # Parse optional banks parameter
    requested_banks = set(query.banks.split(",")) if query.banks else None

    resp: TBankMatchBySignalType = {}
    if query.url:
        if not current_app.config.get("ROLE_HASHER", False):
            abort(403, "Hashing is disabled, missing role")

        hashes = hashing.hash_url_content(
            query.url,
            content_type_hint=query.content_type,
            signal_type_names=query.types,
        )

        for signal_type in hashes.keys():
            signal = hashes[signal_type]
            resp[signal_type] = lookup(signal, signal_type, banks=requested_banks)
    else:
        if not query.signal or not query.signal_type:
            abort(400, "Either url or both signal and signal_type are required")
        matches = lookup(query.signal, query.signal_type, banks=requested_banks)
        return LookupResponse(**matches).model_dump()

    selected_st = query.signal_type
    if selected_st is not None:
        selected_matches = resp.get(selected_st, {})
        return LookupResponse(**selected_matches).model_dump()
    return LookupResponse(**resp).model_dump()


@bp.post(
    "/lookup",
    tags=[Tag(name="Matching")],
    responses={"200": LookupResponse, "400": ErrorResponse, "403": ErrorResponse},
    summary="Content lookup from file",
    description="Look up uploaded file content in the similarity index",
)
def lookup_post() -> ResponseReturnValue:
    """
    Look up the hash for the uploaded file in the similarity index.
    @see OpenMediaMatch.blueprints.hashing hash_media_from_form_data()

    Input:
     * Uploaded file.
     * Optional seed (content id) for consistent coinflip
    Output:
     * JSON object keyed by signal type to bank matches
       (@see lookup_get)
    """
    if not current_app.config.get("ROLE_HASHER", False):
        abort(403, "Hashing is disabled, missing role")

    hashes = hashing.hash_media_from_form_data()
    bypass_coinflip = request.args.get("bypass_coinflip", "false") == "true"

    # Parse optional banks parameter
    banks_param = request.args.get("banks")
    requested_banks = set(banks_param.split(",")) if banks_param else None

    resp = {}
    for signal_type in hashes.keys():
        signal = hashes[signal_type]
        resp[signal_type] = lookup(
            signal, signal_type, bypass_coinflip, requested_banks
        )

    return LookupResponse(**resp).model_dump()


def lookup(
    signal: str,
    signal_type_name: str,
    bypass_coinflip: bool = False,
    banks: t.Optional[t.Set[str]] = None,
) -> TMatchByBank:
    current_app.logger.debug("performing lookup")
    results_by_bank_content_id = {
        r.metadata: r for r in query_index(signal, signal_type_name)
    }
    storage = get_storage()
    current_app.logger.debug("getting bank content")
    contents = storage.bank_content_get(list(results_by_bank_content_id.keys()))
    enabled_content = [c for c in contents if c.enabled]
    current_app.logger.debug(
        "lookup matches %d content ids (%d enabled_content)",
        len(contents),
        len(enabled_content),
    )
    all_banks = {c.bank.name: c.bank for c in enabled_content}

    # Always allow all banks, whether matching is enabled or not if bypass_coinflip is True
    rand = random.Random(request.args.get("seed"))
    coinflip = rand.random() if not bypass_coinflip else 0
    current_app.logger.debug("coinflip: %s", coinflip)
    enabled_banks = {
        b.name for b in all_banks.values() if b.matching_enabled_ratio >= coinflip
    }

    # Filter by requested banks if specified
    if banks is not None:
        enabled_banks = enabled_banks.intersection(banks)

    current_app.logger.debug("enabled_banks: %s", enabled_banks)
    current_app.logger.debug(
        "lookup matches %d banks (%d enabled_banks)", len(all_banks), len(enabled_banks)
    )
    results: TMatchByBank = {}
    for content in enabled_content:
        if content.bank.name not in enabled_banks:
            continue

        matched_content = results_by_bank_content_id[content.id]
        match: MatchWithDistancePayload = {
            "bank_content_id": content.id,
            "distance": matched_content.similarity_info.pretty_str(),
        }
        results.setdefault(content.bank.name, []).append(match)
    return results


@bp.get(
    "/index/status",
    tags=[Tag(name="Matching")],
    responses={"200": IndexStatusResponse, "400": ErrorResponse},
    summary="Index status",
    description="Get the status of matching indices",
)
def index_status() -> ResponseReturnValue:
    """
    Get the status of matching indices.

    You can limit to just a single type with the signal_type parameter.

    Example Output:
    {
        "pdq": {
            "built_to": -1,
            "present": false,
            "size": 0
        },
        "video_md5": {
            "built_to": 1700146048,
            "present": true,
            "size": 591
        }
    }
    """
    storage = get_storage()
    signal_types = storage.get_signal_type_configs()

    limit_to_type = request.args.get("signal_type")
    if limit_to_type is not None:
        if limit_to_type not in signal_types:
            abort(400, f"No such signal type '{limit_to_type}'")
        signal_types = {limit_to_type: signal_types[limit_to_type]}

    status_by_name = {}
    for name, st in signal_types.items():
        checkpoint = storage.get_last_index_build_checkpoint(st.signal_type)

        status = {
            "present": False,
            "built_to": -1,
            "size": 0,
        }
        if checkpoint is not None:
            status = {
                "present": True,
                "built_to": checkpoint.last_item_timestamp,
                "size": checkpoint.total_hash_count,
            }
        status_by_name[name] = status
    return IndexStatusResponse(**status_by_name).model_dump()


@bp.post(
    "/compare",
    tags=[Tag(name="Matching")],
    responses={"200": CompareResponse, "400": ErrorResponse},
    summary="Compare hashes",
    description="Compare pairs of hashes and get the match distance between them",
)
def compare() -> ResponseReturnValue:
    """
    Compare pairs of hashes and get the match distance between them.
    Example input:
    {
        "pdq": ["facd8b...", "facd8b..."],
        "not_pdq": ["bdec19...","bdec19..."]
    }
    Example output
    {
        "pdq": [
            true,
            {
                "distance": 9
            }
        ],
        "not_pdq": 20
            true,
            {
                "distance": 341
            }
        }
    }
    """
    request_data = request.get_json()
    if type(request_data) != dict:
        abort(400, "Request input was not a dict")
    request_model = CompareRequest(**request_data)
    request_data = request_model.model_dump()
    storage = get_storage()
    results = {}
    for signal_type_str in request_data.keys():
        hashes_to_compare = request_data.get(signal_type_str)
        if type(hashes_to_compare) != list:
            abort(400, f"Comparison hashes for {signal_type_str} was not a list")
        if hashes_to_compare.__len__() != 2:
            abort(400, f"Comparison hash list length must be exactly 2")
        signal_type = _validate_and_transform_signal_type(signal_type_str, storage)
        try:
            left = signal_type.validate_signal_str(hashes_to_compare[0])
            right = signal_type.validate_signal_str(hashes_to_compare[1])
            compare_fn = getattr(signal_type, "compare_hash", None)
            if not callable(compare_fn):
                abort(400, f"{signal_type_str} does not support hash comparison")
            comparison_callable = t.cast(t.Callable[[str, str], t.Any], compare_fn)
            comparison = comparison_callable(left, right)
            results[signal_type_str] = comparison
        except Exception as e:
            abort(400, f"Invalid {signal_type_str} hash: {e}")
    return CompareResponse(**results).model_dump()


def initiate_index_cache(app: Flask, scheduler: APScheduler | None) -> None:
    assert not hasattr(app, "signal_type_index_cache"), "Aready initialized?"
    storage = get_storage()
    cache = {
        st.signal_type.get_name(): _SignalIndexInMemoryCache.get_initial(
            st.signal_type, int(app.config.get("INDEX_CACHE_MAX_STALE_SEC", 65))
        )
        for st in storage.get_signal_type_configs().values()
    }
    if scheduler is not None:
        for name, entry in cache.items():
            scheduler.add_job(
                f"Match Index Refresh[{name}]",
                entry.periodic_task,
                trigger="interval",
                seconds=int(app.config.get("TASK_INDEX_CACHE_INTERVAL_SECONDS", 30)),
                start_date=datetime.datetime.now() - datetime.timedelta(seconds=29),
            )
        scheduler.app.logger.info(
            "Added Matcher refresh tasks: %s",
            [f"CachedIndex[{n}]" for n in cache],
        )
    app.signal_type_index_cache = cache  # type: ignore[attr-defined]


def _get_index_cache() -> IndexCache:
    return t.cast(IndexCache, getattr(current_app, "signal_type_index_cache", {}))


def index_cache_is_ready() -> bool:
    return all(idx.is_ready for idx in _get_index_cache().values())


def index_cache_is_stale() -> bool:
    return any(idx.is_stale for idx in _get_index_cache().values())


def _get_index(signal_type: t.Type[SignalType]) -> SignalTypeIndex[int] | None:
    entry = _get_index_cache().get(signal_type.get_name())

    if entry is None:
        current_app.logger.debug("[lookup_signal] no cache, loading index")
        return get_storage().get_signal_type_index(signal_type)
    if entry.is_ready:
        return entry.index
    return None
