# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.extensions.pdq_ocr.pdq_ocr import PdqOcrSignal


TX_MANIFEST = ThreatExchangeExtensionManifest(
    signal_types=(PdqOcrSignal,),
)
