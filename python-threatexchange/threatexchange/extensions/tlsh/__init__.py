# Copyright (c) Meta Platforms, Inc. and affiliates.

from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.extensions.tlsh.text_tlsh import TextTLSHSignal


TX_MANIFEST = ThreatExchangeExtensionManifest(
    signal_types=(TextTLSHSignal,),
)
