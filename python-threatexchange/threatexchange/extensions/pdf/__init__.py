# Copyright (c) Meta Platforms, Inc. and affiliates.

from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.extensions.pdf.content import PDFContent


TX_MANIFEST = ThreatExchangeExtensionManifest(
    content_types=(PDFContent,),
)
