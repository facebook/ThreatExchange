import functools
import typing as t
from dataclasses import asdict, dataclass

import bottle
from mypy_boto3_dynamodb.service_resource import Table

from hmalib.common.config import HMAConfig
from hmalib.common.models.bank import BankMember, BanksTable
from hmalib.indexers.lcc import LCCIndexer
from hmalib.lambdas.api.middleware import DictParseable, JSONifiable, SubApp, jsoninator


@dataclass
class LCCResponse(JSONifiable):
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
def get_index(storage_path, signal_type):
    index = LCCIndexer.get_recent_index(storage_path, signal_type)
    return index


def get_lcc_api(storage_path) -> bottle.Bottle:

    lcc_api = SubApp()

    @lcc_api.get("/", apply=[jsoninator])
    def lcc_hasher() -> LCCResponse:
        index = get_index(storage_path, bottle.request.query.hash.signal_type)
        hash_value = bottle.request.query.hash
        match_array = index.query(hash_value)
        match_value = False
        if len(match_array) != 0:
            match_value = True
        return LCCResponse(match_value, hash_value, match_value[0].metadata)

    return lcc_api
