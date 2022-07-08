# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Helper to allow you to hint at the ThreatExchange type string on SignalTypes
"""

import typing as t


class HasFbThreatExchangeIndicatorType:
    """
    A mixin to hint to fb_threatexchange_api how to handle this SignalType

    For example, PDQSignalType, aka "pdq" in ThreatExchange is "HASH_PDQ"

    We could hardcode all of these into the fetch() method, but that doesn't
    play nicely with expansions. Our solution:

    ```
    class PDQSignalType(SignalType, HasFbThreatExchangeIndicatorType):
        INDICATOR_TYPE = "HASH_PDQ"
        ...
    ```
    """

    INDICATOR_TYPE: t.ClassVar[t.Union[str, t.Tuple[str, ...]]] = ()

    @classmethod
    def facebook_threatexchange_indicator_applies(cls, indicator_type: str) -> bool:
        types = cls.INDICATOR_TYPE
        if isinstance(cls.INDICATOR_TYPE, str):
            types = (cls.INDICATOR_TYPE,)
        return indicator_type in types
