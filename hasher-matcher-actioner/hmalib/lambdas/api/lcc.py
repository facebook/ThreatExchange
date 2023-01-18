# Copyright (c) Meta Platforms, Inc. and affiliates.

import functools
import typing as t
from dataclasses import asdict, dataclass
import bottle

from mypy_boto3_dynamodb.service_resource import Table

from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.signal_type.signal_base import SignalType

from hmalib.common.mappings import HMASignalTypeMapping
from hmalib.indexers.lcc import LCCIndexer
from hmalib.lambdas.api.middleware import DictParseable, JSONifiable, SubApp, jsoninator


@dataclass
class RecentlySeenLCCResponse(JSONifiable):
    found_match: bool
    content_id: t.Optional[str]
    preview_url: t.Optional[str]

    def to_json(self) -> t.Dict:
        return {
            "found_match": self.found_match,
            "content_id": self.content_id,
            "preview_url": self.preview_url,
        }


@functools.lru_cache(maxsize=None)
def get_index(storage_path: str, signal_type_name: str):
    index = LCCIndexer.get_recent_index(storage_path, signal_type_name)
    return index


def get_lcc_api(
    signal_type_mapping: HMASignalTypeMapping, storage_path: str
) -> bottle.Bottle:
    """
    Some APIs to provide live content clustering cabilities. This will index all
    recently seen content and provide a way to query for content_ids matching a
    given hash.
    """

    lcc_api = SubApp()

    @lcc_api.get("/recently-seen/", apply=[jsoninator])
    def recently_seen_in_lcc() -> RecentlySeenLCCResponse:
        """
        Given a signal_type and a hash, have we seen something like this
        recently? Uses default precision knobs.

        TODO: Make thresholds configurable.
        """
        signal_type = signal_type_mapping.get_signal_type_enforce(
            bottle.request.query.signal_type
        )
        hash_value = bottle.request.query.hash

        index = get_index(storage_path, signal_type.get_name())

        match_array = index.query(hash_value)
        found_match = bool(len(match_array))

        if not found_match:
            return RecentlySeenLCCResponse(False, None, None)

        # Use the first result as the content_id, TODO: convert content_Id to
        # preview_url, also add content_type
        content_id = match_array[0].metadata
        preview_url = content_id
        return RecentlySeenLCCResponse(found_match, content_id, preview_url)

    return lcc_api
