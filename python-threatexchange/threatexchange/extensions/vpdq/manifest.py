# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.extensions.vpdq.vpdq import VPDQSignal


TX_MANIFEST = ThreatExchangeExtensionManifest(
    signal_types=(VPDQSignal,),
)
