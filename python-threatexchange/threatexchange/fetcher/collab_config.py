#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Settings used to inform a fetcher what to fetch
"""

import typing as t

from dataclasses import dataclass


@dataclass
class CollaborationConfigBase:
    """
    Settings used to inform a fetcher what to fetch.

    Extend with any additional fields that you need to inform your API how
    and what to fetch.

    Management of persisting these is left to the specific platform
    (i.e. CLI or HMA).
    """

    name: str
    enabled: bool  # Whether to fetch from this or not
    fetcher_name: str  # Fetch_api.SignalExchangeAPI.name()
