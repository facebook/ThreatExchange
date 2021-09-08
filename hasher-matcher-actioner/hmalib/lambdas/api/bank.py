# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle

from mypy_boto3_dynamodb.service_resource import Table

def get_bank_api(bank_table: Table) -> bottle.Bottle:
    """
    Closure for dependencies of the bank API
    """

    bank_api = bottle.Bottle()
    table_manager = BanksTable(table=bank_table)

    return bank_api
