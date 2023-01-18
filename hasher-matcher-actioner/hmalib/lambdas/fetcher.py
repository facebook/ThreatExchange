# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Connect to SignalExchange APIs and download signals, store in banks.
"""
import os
import boto3
from functools import lru_cache

from hmalib.aws_secrets import AWSSecrets
from hmalib.fetching.fetcher import Fetcher
from hmalib.common.logging import get_logger
from hmalib.common.config import HMAConfig
from hmalib.common.models.bank import BanksTable
from hmalib.lambdas.common import get_signal_type_mapping, HMASignalTypeMapping

logger = get_logger(__name__)

BANKS_TABLE = os.environ["BANKS_TABLE"]
CONFIG_TABLE_NAME = os.environ["CONFIG_TABLE_NAME"]
SECRETS_PREFIX = os.environ["SECRETS_PREFIX"]


@lru_cache(maxsize=None)
def get_banks_table(signal_type_mapping: HMASignalTypeMapping):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(BANKS_TABLE)
    return BanksTable(table, signal_type_mapping)


def lambda_handler(_event, _context):
    HMAConfig.initialize(CONFIG_TABLE_NAME)

    signal_type_mapping = get_signal_type_mapping()
    secrets = AWSSecrets(SECRETS_PREFIX)
    fetcher = Fetcher(
        signal_type_mapping, get_banks_table(signal_type_mapping), secrets
    )
    fetcher.run()
