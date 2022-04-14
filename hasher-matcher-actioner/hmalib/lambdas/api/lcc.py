from dataclasses import dataclass, asdict
from mypy_boto3_dynamodb.service_resource import Table
import bottle

from hmalib.common.config import HMAConfig
from hmalib.common.models.bank import BankMember, BanksTable

from hmalib.lambdas.api.middleware import (
    jsoninator,
    JSONifiable,
    DictParseable,
    SubApp,
)

import typing as t


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
        return LCCResponse("", "", "")

    return lcc_api
