# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import sys

if hasattr(sys, "_called_from_test"):
    # called from within a py test run
    pass
else:
    from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
    from threatexchange.extensions.vpdq.video_vpdq import VideoVPDQSignal

    TX_MANIFEST = ThreatExchangeExtensionManifest(
        signal_types=(VideoVPDQSignal,),
    )
