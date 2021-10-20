# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
from dataclasses import dataclass
from hmalib.common.config import HMAConfig


@dataclass
class HashExchangeConfig(HMAConfig):
    """
    Base class for hash exchange configs, this class has common
    properties for all configs.
    """

    fetcher_active: bool
    description: str
    in_use: bool
    write_back: bool
    matcher_active: bool


@dataclass
class ThreatExchangeConfig(HashExchangeConfig):
    """
    Config for ThreatExchange integrations

    Consumed by the fetcher to get data from the right places in
    ThreatExchange, downstream to control write-back information
    like reactions and uploads, and possibly other places that
    need to join HMA and ThreatExchange data.
    """

    privacy_group_name: str

    @property
    def privacy_group_id(self) -> str:
        """TE Configs are keyed by their privacy group ID"""
        return self.name


@dataclass
class NonThreatExchangeConfig(HashExchangeConfig):
    """
    Config for the NonThreatExchange datasets(i.e. StopNCII hashes)
    """

    next_fetch_timestamp: int
