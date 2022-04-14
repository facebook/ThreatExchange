import typing as t
from dataclasses import asdict, dataclass

import bottle
from hmalib.common.config import HMAConfig
from hmalib.common.models.bank import BankMember, BanksTable
from hmalib.lambdas.api.middleware import DictParseable, JSONifiable, SubApp, jsoninator
from mypy_boto3_dynamodb.service_resource import Table


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


def get_lcc_api() -> bottle.Bottle:

    lcc_api = SubApp()

    @lcc_api.get("/", apply=[jsoninator])
    def lcc_hasher() -> LCCResponse:
        print("Hash: ", bottle.request.query.hash)
        return LCCResponse(False, "", "")

    return lcc_api
