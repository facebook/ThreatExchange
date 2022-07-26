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

    Some types might have multiple representations in ThreatExchange, like URL:

    ```
    INDICATOR_TYPE = ("URI", "RAW_URI", "UNCLICKABLE_URL")
    ```

    One of the strengths of ThreatExchange is its flexibility in conventions.
    As long as it takes less than 1MB of storage, we can serialize any data using
    the DEBUG_STRING indicator type. For that, we need to also use the tags feature.
    One convention is to use a `signal_type:` prefix.

    ```
    INDICATOR_TYPE = {"DEBUG_STRING": "signal_type:my_prototype_signal"}
    ```
    Later one it has a real type, you can update to
    ```
    INDICATOR_TYPE = {
        "MY_PROTOTYPE_SIGNAL": None,
        "DEBUG_STRING": "signal_type:my_prototype_signal",
    }
    ```
    """

    INDICATOR_TYPE: t.ClassVar[
        t.Union[str, t.Set[str], t.Dict[str, t.Optional[str]]]
    ] = set()

    @classmethod
    def normalize_fb_threatexchange_indicator(
        cls, tx_type: str, tx_indicator: str, tx_tag: t.Optional[str]
    ) -> str:
        """
        Cleanup signals that might change format depending on type.

        Example:
        RAW_URI: https://www.facebook.com
        UNCLICKABLE_URL: [h]ttps://www.facebook.com

        Post normalized: https://www.facebook.com
        """
        return tx_indicator
