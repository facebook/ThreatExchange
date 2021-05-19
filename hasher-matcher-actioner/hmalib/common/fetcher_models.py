# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
from dataclasses import dataclass
from hmalib.common.config import HMAConfig


@dataclass
class ThreatExchangeConfig(HMAConfig):
    """
    Config for ThreatExchange integrations

    Consumed by the fetcher to get data from the right places in
    ThreatExchange, downstream to control write-back information
    like reactions and uploads, and possibly other places that
    need to join HMA and ThreatExchange data.
    """

    # TODO - consider hiding name field and always populating with ID
    fetcher_active: bool
    privacy_group_name: str
    description: str
    in_use: bool
    write_back: bool
    matcher_active: bool

    @property
    def privacy_group_id(self) -> str:
        """TE Configs are keyed by their privacy group ID"""
        return self.name
