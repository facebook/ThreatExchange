# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Endpoints for matching content and hashes.
"""

from collections import defaultdict
from dataclasses import dataclass
import datetime
import random
import typing as t
import time

from flask import Blueprint, Flask, abort, current_app, request
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
    require_request_param,
    str_to_bool,
)
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.utils.memory_utils import trim_process_memory

bp = Blueprint("matching", __name__)
bp.register_error_handler(HTTPException, api_error_handler)


# Type helpers


class MatchWithDistance(t.TypedDict):
    bank_content_id: int
    distance: str


class MatchWithDistanceAndSignal(t.TypedDict):
    bank_content_id: int
    distance: str
    signal: str


TMatchByBank = t.Mapping[str, t.Sequence[MatchWithDistance]]
TBankMatchBySignalType = t.Mapping[str, TMatchByBank]


@dataclass
class _SignalIndexInMemoryCache:
    signal_type: t.Type[SignalType]
    index: SignalTypeIndex[int]
    checkpoint: interface.SignalTypeIndexBuildCheckpoint
    last_check_ts: float

    @property
    def is_ready(self):
        return self.last_check_ts > 0

    @property
    def is_stale(self):
        """
        If we are overdue on refresh by too long, consider it stale.
        """
        return time.time() - self.last_check_ts > 65

    @classmethod
    def get_initial(cls, signal_type: t.Type[SignalType]) -> t.Self:
        return cls(
            signal_type,
            signal_type.get_index_cls().build([]),
            interface.SignalTypeIndexBuildCheckpoint.get_empty(),
            0,
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


@bp.route("/raw_lookup")
def raw_lookup():
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
    signal = require_request_param("signal")
    signal_type_name = require_request_param("signal_type")
    include_distance = str_to_bool(request.args.get("include_distance", "false"))
    lookup_signal_func = (
        lookup_signal_with_distance if include_distance else lookup_signal
    )

    return {"matches": lookup_signal_func(signal, signal_type_name)}


@bp.route("/lookup_threshold")
def lookup_threshold():
    """
    Look up a hash in the similarity index using a custom threshold.

    This endpoint allows querying with a specific similarity threshold
    instead of using the default threshold for the signal type.

    Input:
     * Signal type (hash type)
     * Signal value (the hash)
     * Threshold (int) - maximum distance for matches (required)
    Output:
     * List of matching with content_id, distance, and signal values
    """
    signal = require_request_param("signal")
    signal_type_name = require_request_param("signal_type")
    threshold = int(require_request_param("threshold"))

    results = query_index_threshold(signal, signal_type_name, threshold)
    storage = get_storage()
    # Get signals for the results
    content_ids = [m.metadata for m in results]
    signals_by_content = storage.bank_content_get_signals(content_ids)
    matches = [
        {
            "bank_content_id": m.metadata,
            "distance": m.similarity_info.pretty_str(),
            "signal": signals_by_content.get(m.metadata, {}).get(signal_type_name, ""),
        }
        for m in results
    ]
    return {"matches": matches}


@bp.route("/lookup_topk")
def lookup_topk():
    """
    Look up the top K closest matches for a hash in the similarity index.

    This endpoint returns the K closest matches regardless of threshold.

    Input:
     * Signal type (hash type)
     * Signal value (the hash)
     * k (int) - number of top matches to return (required)
    Output:
     * List of matching with content_id, distance, and signal values
    """
    signal = require_request_param("signal")
    signal_type_name = require_request_param("signal_type")
    k = int(require_request_param("k"))

    results = query_index_topk(signal, signal_type_name, k)
    storage = get_storage()
    # Get signals for the results
    content_ids = [m.metadata for m in results]
    signals_by_content = storage.bank_content_get_signals(content_ids)
    matches = [
        {
            "bank_content_id": m.metadata,
            "distance": m.similarity_info.pretty_str(),
            "signal": signals_by_content.get(m.metadata, {}).get(signal_type_name, ""),
        }
        for m in results
    ]
    return {"matches": matches}


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


def query_index_threshold(
    signal: str, signal_type_name: str, threshold: int
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
    if not hasattr(index, 'query_threshold'):
        abort(501, f"Signal type '{signal_type_name}' does not support query_threshold method")
    current_app.logger.debug("[lookup_signal_threshold] querying index")
    results = index.query_threshold(signal, threshold)
    current_app.logger.debug("[lookup_signal_threshold] query complete")
    return results


def query_index_topk(
    signal: str, signal_type_name: str, k: int
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
    if not hasattr(index, 'query_top_k'):
        abort(501, f"Signal type '{signal_type_name}' does not support query_top_k method")
    current_app.logger.debug("[lookup_signal_topk] querying index")
    results = index.query_top_k(signal, k)
    current_app.logger.debug("[lookup_signal_topk] query complete")
    return results


def lookup_signal(signal: str, signal_type_name: str) -> list[int]:
    results = query_index(signal, signal_type_name)
    return [m.metadata for m in results]


def lookup_signal_with_distance(
    signal: str, signal_type_name: str
) -> list[MatchWithDistance]:
    results = query_index(signal, signal_type_name)
    return [
        {
            "bank_content_id": m.metadata,
            "distance": m.similarity_info.pretty_str(),
        }
        for m in results
    ]


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


@bp.route("/lookup", methods=["GET"])
def lookup_get() -> t.Union[TMatchByBank, TBankMatchBySignalType]:
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
    resp: dict[str, TMatchByBank] = {}
    if request.args.get("url", None):
        if not current_app.config.get("ROLE_HASHER", False):
            abort(403, "Hashing is disabled, missing role")

        hashes = hashing.hash_media()

        for signal_type in hashes.keys():
            signal = hashes[signal_type]
            resp[signal_type] = lookup(signal, signal_type)
    else:
        signal = require_request_param("signal")
        signal_type = require_request_param("signal_type")
        return lookup(signal, signal_type)

    selected_st = request.args.get("signal_type")
    if selected_st is not None:
        return resp[selected_st]
    return resp


@bp.route("/lookup", methods=["POST"])
def lookup_post() -> TBankMatchBySignalType:
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

    resp = {}
    for signal_type in hashes.keys():
        signal = hashes[signal_type]
        resp[signal_type] = lookup(signal, signal_type, bypass_coinflip)

    return resp


def lookup(
    signal: str, signal_type_name: str, bypass_coinflip: bool = False
) -> TMatchByBank:
    current_app.logger.debug("performing lookup")
    results_by_bank_content_id = {
        r.metadata: r for r in query_index(signal, signal_type_name)
    }
    storage = get_storage()
    current_app.logger.debug("getting bank content")
    contents = storage.bank_content_get(results_by_bank_content_id)
    enabled_content = [c for c in contents if c.enabled]
    current_app.logger.debug(
        "lookup matches %d content ids (%d enabled_content)",
        len(contents),
        len(enabled_content),
    )
    banks = {c.bank.name: c.bank for c in enabled_content}

    # Always allow all banks, whether matching is enabled or not if bypass_coinflip is True
    rand = random.Random(request.args.get("seed"))
    coinflip = rand.random() if not bypass_coinflip else 0
    current_app.logger.debug("coinflip: %s", coinflip)
    enabled_banks = {
        b.name for b in banks.values() if b.matching_enabled_ratio >= coinflip
    }
    current_app.logger.debug("enabled_banks: %s", enabled_banks)
    current_app.logger.debug(
        "lookup matches %d banks (%d enabled_banks)", len(banks), len(enabled_banks)
    )
    results = defaultdict(list)
    for content in enabled_content:
        if content.bank.name not in enabled_banks:
            continue

        matched_content = results_by_bank_content_id[content.id]
        match: MatchWithDistance = {
            "bank_content_id": content.id,
            "distance": matched_content.similarity_info.pretty_str(),
        }
        results[content.bank.name].append(match)
    return results


@bp.route("/index/status")
def index_status():
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
    return status_by_name


@bp.route("/compare", methods=["POST"])
def compare():
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
    storage = get_storage()
    results = {}
    for signal_type_str in request_data.keys():
        hashes_to_compare = request_data.get(signal_type_str)
        if type(hashes_to_compare) != list:
            abort(400, f"Comparison hashes for {signal_type_str} was not a list")
        if hashes_to_compare.__len__() != 2:
            abort(400, f"Comparison hash list lenght must be exactly 2")
        signal_type = _validate_and_transform_signal_type(signal_type_str, storage)
        try:
            left = signal_type.validate_signal_str(hashes_to_compare[0])
            right = signal_type.validate_signal_str(hashes_to_compare[1])
            comparison = signal_type.compare_hash(left, right)
            results[signal_type_str] = comparison
        except Exception as e:
            abort(400, f"Invalid {signal_type_str} hash: {e}")
    return results


def initiate_index_cache(app: Flask, scheduler: APScheduler | None) -> None:
    assert not hasattr(app, "signal_type_index_cache"), "Aready initialized?"
    storage = get_storage()
    cache = {
        st.signal_type.get_name(): _SignalIndexInMemoryCache.get_initial(st.signal_type)
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
