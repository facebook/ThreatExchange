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
from threatexchange.exchanges import auth
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.storage.interfaces import (
    BankContentConfig as _BankContentConfig,
    IUnifiedStore as _IUnifiedStore,
)

# Where the credentials used for an exchange came from, in resolution order.
# "environment" and "file" are the CredentialHelper fallbacks consulted by the
# API class itself when no stored credentials are passed to for_collab().
CredentialSource = t.Literal["exchange", "api", "environment", "file"]


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

    def exchange_credentials_supported(self) -> bool:
        """Whether exchange_set_credentials() is implemented by this store."""
        return False

    def exchange_get_credentials(self, name: str) -> t.Optional[auth.CredentialHelper]:
        """
        Get the credentials stored on a single exchange, if any.

        Returns None if the exchange doesn't exist or has no credentials of its
        own. Stores that don't support per-exchange credentials can keep this
        default, and will only use API-level and environment credentials.
        """
        return None

    def exchange_set_credentials(
        self, name: str, credentials: t.Optional[auth.CredentialHelper]
    ) -> None:
        """
        Set (or clear, if None) the credentials for a single exchange.

        Throws KeyError if the exchange doesn't exist, and ValueError if the
        credentials are the wrong type for the exchange's API.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} doesn't support per-exchange credentials"
        )

    def exchange_get_resolved_credentials(
        self, collab: CollaborationConfigBase
    ) -> t.Tuple[t.Optional[auth.CredentialHelper], t.Optional[CredentialSource]]:
        """
        The stored credentials that should be used for this exchange.

        The exchange's own credentials win, then the per-API-type credentials.
        If this returns (None, None), the API class falls back to its own
        discovery (environment variables, files).
        """
        creds = self.exchange_get_credentials(collab.name)
        if creds is not None:
            return creds, "exchange"
        api_cfg = self.exchange_apis_get_configs().get(collab.api)
        if api_cfg is not None and api_cfg.credentials is not None:
            return api_cfg.credentials, "api"
        return None, None

    def init_flask(self, app: flask.Flask) -> None:
        """
        Make any flask-specific initialization for this storage implementation.

        This serves as the normal constructor when used with OMM, which allows
        you to write __init__ how is most useful to your implementation for
        testing.
        """
        return
