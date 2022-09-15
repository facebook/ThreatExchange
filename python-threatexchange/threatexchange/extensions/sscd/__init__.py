from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest

from threatexchange.extensions.sscd.sscd_signal import SSCDSignal


TX_MANIFEST = ThreatExchangeExtensionManifest(
    signal_types=(SSCDSignal,),
)
# TODO - installation instructions for torchscript
