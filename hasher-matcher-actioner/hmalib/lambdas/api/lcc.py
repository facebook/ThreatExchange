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


# I return this type because I saw in the documentation that a
# to_json method is required

# I might need to use
# `jsoninator(<requestObj>, from_query=True)` but not sure how the from_query=True
# would modify this implementation
@dataclass
class LccResponse(JSONifiable):
    found_match: bool
    content_id: t.Optional[str]
    preview_url: t.Optional[str]

    def to_json(self) -> t.Dict:
        return {
            "found_match": self.found_match,
            "content_id": self.content_id,
            "preview_url": self.preview_url,
        }

    # def to_json(self) -> t.Dict:
    #     return asdict(self)


def get_lcc_api(
    datastore_table: Table,
    hma_config_table: str,
    indexes_bucket_name: str,
    writeback_queue_url: str,
    bank_table: Table,
    hash_queue_url: str,
) -> bottle.Bottle:

    lcc_api = SubApp()

    # Not sure if I need these two?
    HMAConfig.initialize(hma_config_table)
    banks_table = BanksTable(table=bank_table)

    @lcc_api.get("/", apply=[jsoninator])
    def lcc_hasher() -> LccResponse:
        # Do i need a case if these are blank?
        # They seem to default to "" if left out in the api request
        found_match = bottle.request.query.found_match
        content_id = bottle.request.query.content_id
        preview_url = bottle.request.query.preview_url
        return LccResponse(found_match, content_id, preview_url)

    return lcc_api
