# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
from dataclasses import dataclass

from hmalib.lambdas.api.middleware import JSONifiable
from hmalib.common.models.bank import Bank


@dataclass
class AllBanksEnvelope(JSONifiable):
    banks: t.List[Bank]

    def to_json(self) -> t.Dict:
        return {"banks": [bank.to_json() for bank in self.banks]}
