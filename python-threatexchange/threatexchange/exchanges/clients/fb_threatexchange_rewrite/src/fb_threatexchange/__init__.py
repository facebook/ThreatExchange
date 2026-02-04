"""
fb_threatexchange - A Python library for ThreatExchange integration.

This library provides utilities for working with Meta's ThreatExchange platform.
"""

__version__ = "0.1.0"
__author__ = "Jeff Gong"
__email__ = "jeffgong@meta.com"

from fb_threatexchange.core import ThreatExchangeClient
from fb_threatexchange.models import ThreatDescriptor, ThreatIndicator

__all__ = [
    "ThreatExchangeClient",
    "ThreatDescriptor",
    "ThreatIndicator",
    "__version__",
]

