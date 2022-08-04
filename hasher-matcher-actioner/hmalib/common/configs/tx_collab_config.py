# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
DynamoDB backed CollaborationConfig objects.

This may become a CollaborationConfigStoreBase, but since none of the pytx
interfaces require it, keeping it as just another class for now.
"""

import typing as t
import itertools

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.signal_exchange_api import SignalExchangeAPI

from hmalib.common.config import HMAConfig, create_config


def make_collab_config_subclass(
    cls: t.Type[CollaborationConfigBase],
) -> t.Type[HMAConfig]:
    """
    Generate an HMAConfig subclass on-the-fly.

    Since supported APIs are dynamic, we need to allow any
    CollaborationConfigBase to be stored as an HMAConfig object.
    """
    return type(f"_Dynamic{cls.__name__}_HMAConfig", (cls, HMAConfig), {})


def get_all(apis: t.List[t.Type[SignalExchangeAPI]]) -> t.List[CollaborationConfigBase]:
    """Get all collaboration configs. Across provided SignalExchangeAPI types."""
    all_collab_config_classes = [
        make_collab_config_subclass(api.get_config_class()) for api in apis
    ]

    # itertools.chain.from_iterable flattens a 2d list into a 1d list.
    return list(
        itertools.chain.from_iterable(
            [cc_class.get_all() for cc_class in all_collab_config_classes]
        )
    )


def create_config_for_api(api: t.Type[SignalExchangeAPI], values: t.Dict[str, t.Any]):
    cls = make_collab_config_subclass(api.get_config_class())
    create_config(cls(**values))
