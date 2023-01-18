# Copyright (c) Meta Platforms, Inc. and affiliates.

from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.extensions.pdq_ocr.pdq_ocr import PdqOcrSignal


TX_MANIFEST = ThreatExchangeExtensionManifest(
    signal_types=(PdqOcrSignal,),
)
