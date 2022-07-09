# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.extensions.pdf.pdq import PDFContentType


TX_MANIFEST = ThreatExchangeExtensionManifest(
    content_types=(PDFContentType,),
)
