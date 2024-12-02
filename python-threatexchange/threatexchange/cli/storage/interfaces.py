# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Common interface for persisting pytx configuration and concepts.

Most of the individual components of pytx are find to use piecemeal, and
the full interface covers the most complex and complete useage. A usecase
with one collection of hashes using one algorithm might be better off 
hardcoding those things rather than fully implementing the interface.

# Migration Notes
There's an earlier attempt at these interfaces used for CLI at
<@Mackay-Fisher add the right pointer to the CLI storage>.
During the development of Hasher-Matcher-Actioner 2.0 
(github.com/facebook/ThreatExchange/tree/main/hasher-matcher-actioner/)
we realized that the original attempt at this wouldn't meet the needs
of that code and wrote a new interface. 

As of 12/2024, we are now migrating that interface from HMA into pytx
proper as part of a migration to dbm 
(github.com/facebook/ThreatExchange/issues/1687). The general approach is:
1. Copy the interface unchanged from HMA to pytx
2. Release a new version of pytx
3. Delete the copy in HMA and update all references to the pytx version

In parallel, we intend to slowly migrate the CLI storage components to
follow the same interface.
"""

import abc
from dataclasses import dataclass
import typing as t
from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import SignalType


@dataclass
class SignalTypeConfig:
    """
    Holder for SignalType configuration
    """

    # Signal types that are not enabled should not be used in hashing/matching
    enabled_ratio: float
    signal_type: t.Type[SignalType]

    @property
    def enabled(self) -> bool:
        # TODO do a coin flip here, but also refactor this to do seeding
        return self.enabled_ratio >= 0.0


class ISignalTypeConfigStore(metaclass=abc.ABCMeta):
    """Interface for accessing SignalType configuration"""

    @abc.abstractmethod
    def get_signal_type_configs(self) -> t.Mapping[str, SignalTypeConfig]:
        """Return all installed signal types."""

    @abc.abstractmethod
    def _create_or_update_signal_type_override(
        self, signal_type: str, enabled_ratio: float
    ) -> None:
        """Create or update database entry for a signal type, setting a new value."""

    @t.final
    def create_or_update_signal_type_override(
        self, signal_type: str, enabled_ratio: float
    ) -> None:
        """Update enabled ratio of an installed signal type."""
        installed_signal_types = self.get_signal_type_configs()
        if signal_type not in installed_signal_types:
            raise ValueError(f"Unknown signal type {signal_type}")
        if not (0.0 <= enabled_ratio <= 1.0):
            raise ValueError(
                f"Invalid enabled ratio {enabled_ratio}. Must be in the range 0.0-1.0 inclusive."
            )
        self._create_or_update_signal_type_override(signal_type, enabled_ratio)

    @t.final
    def get_enabled_signal_types(self) -> t.Mapping[str, t.Type[SignalType]]:
        """Helper shortcut for getting only enabled SignalTypes"""
        return {
            k: v.signal_type
            for k, v in self.get_signal_type_configs().items()
            if v.enabled
        }

    @t.final
    def get_enabled_signal_types_for_content_type(
        self, content_type: t.Type[ContentType]
    ) -> t.Mapping[str, t.Type[SignalType]]:
        """Helper shortcut for getting enabled types for a piece of content"""
        return {
            k: v.signal_type
            for k, v in self.get_signal_type_configs().items()
            if v.enabled and content_type in v.signal_type.get_content_types()
        }
