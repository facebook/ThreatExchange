#  Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Helpers for handling authentification and credentials for SignalExchangeAPI
"""

from abc import ABCMeta, abstractmethod
import contextlib
import logging
import os
import pathlib
import typing as t

from threatexchange.exchanges.signal_exchange_api import (
    AnySignalExchangeAPI,
    TCollabConfig,
)


class SignalExchangeAPIInvalidAuthException(Exception):
    """
    An exception you can use to hint users their authentification is bad

    This can be because it's incorrectly formatted, it's been expired,
    or a multitude of other reasons.
    """

    def __init__(self, src_api: t.Type[AnySignalExchangeAPI], message: str) -> None:
        self.src_api = src_api
        self.message = message


class SignalExchangeAPIMissingAuthException(Exception):
    """
    An exception you can use to hint users how to authentificate your API
    """

    def __init__(
        self,
        src_api: t.Type[AnySignalExchangeAPI],
        *,
        file_hint: str = "",
        env_hint: str = "",
    ) -> None:
        self.src_api = src_api
        self.hints: t.List[str] = []
        if env_hint:
            self.add_env_hint(env_hint)
        if file_hint:
            self.add_file_hint(file_hint)

    def add_file_hint(self, filename: str) -> None:
        self.hints.append(
            f"creating (and maybe `chmod 400`) a file with credentials at {filename}"
        )

    def add_env_hint(self, variable_name: str) -> None:
        self.hints.append(f"populating an environment variable called {variable_name}")

    def pretty_str(self) -> str:
        lines = [
            f"Couldn't authenticate {self.src_api.get_name()}, "
            "it's missing authentification!"
        ]
        if self.hints:
            lines.append("You can fix this by:")
            for i, hint in enumerate(self.hints, 1):
                lines.append(f"  {i}. {hint}")
        return "\n".join(lines)


CredentialSelf = t.TypeVar("CredentialSelf", bound="CredentialHelper")


class CredentialHelper:
    """
    Wrapper to help standardize credential sources, and tie to exceptions
    """

    ENV_VARIABLE: t.ClassVar[str] = ""
    FILE_NAME: t.ClassVar[str] = ""

    # This is slated to be removed in a future version!
    # It's a placeholder approach while for_collab() gains the auth argument
    _DEFAULT: t.ClassVar[t.Optional["CredentialHelper"]] = None  # t.Self
    _DEFAULT_SRC: t.ClassVar[str] = ""

    @classmethod
    def get(
        cls: t.Type[CredentialSelf], for_cls: t.Type[AnySignalExchangeAPI]
    ) -> CredentialSelf:
        srcs: t.List[t.Tuple[t.Callable[[], t.Optional[CredentialSelf]], str]] = [
            ((lambda: cls._DEFAULT), cls._DEFAULT_SRC),  # type: ignore[list-item,return-value]
            (cls._from_env, f"environment variable {cls.ENV_VARIABLE}"),
            (cls._from_file, f"file {cls.FILE_NAME}"),
        ]
        for fn, src in srcs:
            try:
                creds = fn()
                if creds is None:
                    continue
                if creds._are_valid():
                    return creds
            except Exception:
                logging.exception("Exception during parsing %s", src)
                pass
            raise SignalExchangeAPIInvalidAuthException(
                for_cls, f"Invalid credentials from {src}"
            )
        ex = SignalExchangeAPIMissingAuthException(for_cls)
        if cls._DEFAULT_SRC:
            ex.hints.append(cls._DEFAULT_SRC)
        if cls.ENV_VARIABLE:
            ex.add_env_hint(cls.ENV_VARIABLE)
        if cls.FILE_NAME:
            ex.add_file_hint(cls.FILE_NAME)
        raise ex

    @classmethod
    def set_default(
        cls: t.Type[CredentialSelf], new_default: t.Optional[CredentialSelf], src: str
    ) -> t.ContextManager[None]:
        """
        Set the default (highest preferred) credentials manually.

        They won't be checked for validity until a future get()

        This call can be used as contextmanager to unset within a `with` statement
        """
        cls._DEFAULT = new_default
        cls._DEFAULT_SRC = src
        return cls._unset_default_context()

    @classmethod
    @contextlib.contextmanager
    def _unset_default_context(cls: t.Type[CredentialSelf]) -> t.Iterator[None]:
        yield
        cls.clear_default()

    @classmethod
    def clear_default(cls) -> None:
        """Reset the default"""
        cls.set_default(None, "")

    @classmethod
    def _from_str(cls: t.Type[CredentialSelf], s: str) -> t.Optional[CredentialSelf]:
        """Parse credentials from a string"""
        return None

    @classmethod
    def _from_file(cls: t.Type[CredentialSelf]) -> t.Optional[CredentialSelf]:
        """Parse credentials from a file"""
        if not cls.FILE_NAME:
            return None
        path = pathlib.Path(cls.FILE_NAME).expanduser()
        if not path.is_file():
            return None
        return cls._from_str(path.read_text().strip())

    @classmethod
    def _from_env(cls: t.Type[CredentialSelf]) -> t.Optional[CredentialSelf]:
        """Parse credentials from an environment variable"""
        if not cls.ENV_VARIABLE:
            return None
        s = os.environ.get(cls.ENV_VARIABLE)
        if not s:
            return None
        return cls._from_str(s)

    def _are_valid(self) -> bool:
        return True


TCredentials = t.TypeVar("TCredentials", bound=CredentialHelper)
Self = t.TypeVar("Self")


class SignalExchangeWithAuth(t.Generic[TCollabConfig, TCredentials], metaclass=ABCMeta):
    """
    A mixin for SignalExchange APIs that need authentification/credentials

    The promises made by for_collab are the same - if no credentials are passed in,
    the class can search for its own credentials (though the CredentialHelper class
    makes it easy to do there).
    """

    @staticmethod
    @abstractmethod
    def get_credential_cls() -> t.Type[TCredentials]:
        pass

    @classmethod
    @abstractmethod
    def for_collab(
        cls: t.Type[Self],
        collab: TCollabConfig,
        credentials: t.Optional[TCredentials] = None,
    ) -> Self:
        """
        @see SignalExchangeAPI.for_collab

        If credentials are passed in, the API should use those rather than
        trying to discover its own.
        """
        pass
