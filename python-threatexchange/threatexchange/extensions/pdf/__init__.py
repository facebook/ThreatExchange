# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.extensions.pdf.content import PDFContent


TX_MANIFEST = ThreatExchangeExtensionManifest(
    content_types=(PDFContent,),
)
