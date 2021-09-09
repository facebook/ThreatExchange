# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle
import typing as t
from dataclasses import dataclass

from mypy_boto3_dynamodb.service_resource import Table

from hmalib.common.models.bank import Bank, BanksTable

from .middleware import jsoninator, JSONifiable


@dataclass
class AllBanksEnvelope(JSONifiable):
    banks: t.List[Bank]

    def to_json(self) -> t.Dict:
        return {"banks": [bank.to_json() for bank in self.banks]}


def get_bank_api(bank_table: Table) -> bottle.Bottle:
    """
    Closure for dependencies of the bank API
    """

    bank_api = bottle.Bottle()
    table_manager = BanksTable(table=bank_table)

    @bank_api.get("/get-all-banks", apply=[jsoninator])
    def get_all_banks() -> AllBanksEnvelope:
        """
        Get all banks.
        """
        return AllBanksEnvelope(banks=table_manager.get_all_banks())

    @bank_api.get("/get-bank/<bank_id>", apply=[jsoninator])
    def get_bank(bank_id=None) -> Bank:
        """
        Get a specific bank from a bank_id.
        """
        bank = table_manager.get_bank(bank_id=bank_id)
        return bank

    @bank_api.post("/create-bank", apply=[jsoninator])
    def create_bank() -> Bank:
        """
        Create a bank using only the name and description.
        """
        return table_manager.create_bank(
            bank_name=bottle.request.json["bank_name"],
            bank_description=bottle.request.json["bank_description"],
        )

    @bank_api.post("/update-bank/<bank_id>", apply=[jsoninator])
    def update_bank(bank_id=None) -> Bank:
        """
        Update name and description for a bank_id.
        """
        return table_manager.update_bank(
            bank_id=bank_id,
            bank_name=bottle.request.json["bank_name"],
            bank_description=bottle.request.json["bank_description"],
        )

    return bank_api
