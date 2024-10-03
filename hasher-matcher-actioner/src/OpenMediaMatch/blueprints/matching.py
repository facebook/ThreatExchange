# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Endpoints for matching content and hashes.
"""

from dataclasses import dataclass
import datetime
import random
import sys
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

bp = Blueprint("matching", __name__)
bp.register_error_handler(HTTPException, api_error_handler)


class MatchWithDistance(t.TypedDict):
    content_id: int
    distance: str


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
        curr_checkpoint = store.get_last_index_build_checkpoint(
            self.signal_type)
        if curr_checkpoint is not None and self.checkpoint != curr_checkpoint:
            new_index = store.get_signal_type_index(self.signal_type)
            assert new_index is not None
            self.index = new_index
            self.checkpoint = curr_checkpoint
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
    Look up a hash in the similarity index
    Input:
     * Signal type (hash type)
     * Signal value (the hash)
     * Optional list of banks to restrict search to
     * Optional include_distance (bool) wether or not to return distance values on match
    Output:
     * List of matching with content_id and, if included, distance values
    """
    signal = require_request_param("signal")
    signal_type_name = require_request_param("signal_type")
    include_distance = str_to_bool(
        request.args.get("include_distance", "false"))
    lookup_signal_func = (
        lookup_signal_with_distance if include_distance else lookup_signal
    )

    return {"matches": lookup_signal_func(signal, signal_type_name)}


def query_index(
    signal: str, signal_type_name: str
) -> t.Sequence[IndexMatchUntyped[SignalSimilarityInfo, int]]:
    storage = get_storage()
    signal_type = _validate_and_transform_signal_type(
        signal_type_name, storage)

    try:
        signal = signal_type.validate_signal_str(signal)
    except Exception as e:
        abort(400, f"invalid signal type: {e}")

    index = _get_index(signal_type)

    if index is None:
        abort(503, "index not yet ready")
    current_app.logger.debug("[lookup_signal] querying index")
    results = index.query(signal)
    current_app.logger.debug("[lookup_signal] query complete")
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
            "content_id": m.metadata,
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
def lookup_get():
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
     * List of matching banks
    """
    # Url was passed as a query param?
    if request.args.get("url", None):
        hashes = hashing.hash_media()
        resp = {}
        for signal_type in hashes.keys():
            signal = hashes[signal_type]
            resp[signal_type] = lookup(signal, signal_type)
    else:
        signal = require_request_param("signal")
        signal_type = require_request_param("signal_type")
        resp = lookup(signal, signal_type)

    return resp


@bp.route("/lookup", methods=["POST"])
def lookup_post():
    """
    Look up the hash for the uploaded file in the similarity index.
    @see OpenMediaMatch.blueprints.hashing hash_media_post()

    Input:
     * Uploaded file.
     * Optional seed (content id) for consistent coinflip
    Output:
     * List of matching banks
    """
    hashes = hashing.hash_media_post()

    resp = {}
    for signal_type in hashes.keys():
        signal = hashes[signal_type]
        resp[signal_type] = lookup(signal, signal_type)

    return resp


def lookup(signal, signal_type_name):
    current_app.logger.debug("performing lookup")
    raw_results = lookup_signal(signal, signal_type_name)
    storage = get_storage()
    current_app.logger.debug("getting bank content")
    current_app.logger.debug(raw_results)
    contents = storage.bank_content_get(
        raw_results
    )
    enabled = [c for c in contents if c.enabled]
    current_app.logger.debug(
        "lookup matches %d content ids (%d enabled)", len(
            contents), len(enabled)
    )
    if not enabled:
        return []
    banks = {c.bank.name: c.bank for c in enabled}
    rand = random.Random(request.args.get("seed"))
    coinflip = rand.random()
    enabled_banks = [
        b.name for b in banks.values() if b.matching_enabled_ratio >= coinflip
    ]
    current_app.logger.debug(
        "lookup matches %d banks (%d enabled)", len(banks), len(enabled_banks)
    )
    return enabled_banks


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
                seconds=30,
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
