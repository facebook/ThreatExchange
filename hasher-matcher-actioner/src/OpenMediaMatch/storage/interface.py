# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Abstraction layer for fetching information needed to run OMM.

The base interfaces have been migrated to the threatexchange library
(threatexchange.storage.interfaces). This module re-exports those interfaces
and adds OMM-specific extensions.
"""

import abc
from dataclasses import dataclass
import typing as t

import flask
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.storage.interfaces import (
    BankContentConfig as _BankContentConfig,
    IUnifiedStore as _IUnifiedStore,
)


# TODO: Merge into pytx, and remove this version
@dataclass
class BankContentConfig(_BankContentConfig):
    """
    OMM extension of BankContentConfig adding user-supplied metadata and notes.

    TODO: Complete merging user metadata into the
    """

    # User-supplied metadata from POST /bank/<name>/content (content_id, content_uri, json).
    # Returned on GET when include_metadata is true.
    user_metadata: t.Optional[t.Dict[str, t.Any]] = None

    note: t.Optional[str] = None


class IFlaskUnifiedStore(
    _IUnifiedStore,
    metaclass=abc.ABCMeta,
):
    """
    All the store classes combined into one interface, extended with OMM-specific hooks.
    """

    # TODO: Merge into pytx, remove this version
    @abc.abstractmethod
    def bank_content_get(self, id: t.Iterable[int]) -> t.Sequence[BankContentConfig]:
        """Get the content config for a bank."""

    # TODO: Merge into pytx, remove this version
    @abc.abstractmethod
    def bank_content_update(
        self, val: BankContentConfig  # type: ignore[override]
    ) -> None:
        """Update the content config for a bank"""

    # TODO: Merge into pytx, remove this version
    @abc.abstractmethod
    def bank_add_content(  # type: ignore[override]
        self,
        bank_name: str,
        content_signals: t.Dict[t.Type[SignalType], str],
        config: t.Optional[BankContentConfig] = None,
    ) -> int:
        """Add content to a bank."""

    def init_flask(self, app: flask.Flask) -> None:
        """
        Make any flask-specific initialization for this storage implementation.

        This serves as the normal constructor when used with OMM, which allows
        you to write __init__ how is most useful to your implementation for
        testing.
        """
        return
