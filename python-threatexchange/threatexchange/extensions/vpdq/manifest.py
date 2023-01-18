# Copyright (c) Meta Platforms, Inc. and affiliates.

from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.extensions.vpdq.vpdq import VPDQSignal


TX_MANIFEST = ThreatExchangeExtensionManifest(
    signal_types=(VPDQSignal,),
)
