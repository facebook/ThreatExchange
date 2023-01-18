# Copyright (c) Meta Platforms, Inc. and affiliates.
from dataclasses import dataclass
from hmalib.common.config import HMAConfig


@dataclass
class HashExchangeConfig(HMAConfig):
    """
    Base class for hash exchange configs, this class has common
    properties for all config types. Consumed by the fetcher to
    get hash data , downstream to control write-back information
    like reactions and uploads, and possibly other places that
    need to join HMA and hash data.
    """

    fetcher_active: bool
    description: str
    in_use: bool
    write_back: bool
    matcher_active: bool


@dataclass
class ThreatExchangeConfig(HashExchangeConfig):
    """
    Config for ThreatExchange datasets.
    """

    privacy_group_name: str

    @property
    def privacy_group_id(self) -> str:
        """TE Configs are keyed by their privacy group ID"""
        return self.name


@dataclass
class AdditionalMatchSettingsConfig(HMAConfig):
    """
    This object is stop gap until ThreatExchangeConfig and this class
    can be consolidated into a Bank and utilize a banks settings.

    The reason `pdq_match_threshold` is not added to ThreatExchangeConfig
    directly is the field is optional and HMAConfig will error for all configs
    without it.
    """

    pdq_match_threshold: int


@dataclass
class NonThreatExchangeConfig(HashExchangeConfig):
    """
    Config for the NonThreatExchange datasets.
    """

    next_fetch_timestamp: int
