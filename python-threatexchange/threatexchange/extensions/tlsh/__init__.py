# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.extensions.tlsh.text_tlsh import TextTLSHSignal


TX_MANIFEST = ThreatExchangeExtensionManifest(
    signal_types=(TextTLSHSignal,),
)
