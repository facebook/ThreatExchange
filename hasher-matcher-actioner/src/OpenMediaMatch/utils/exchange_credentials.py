# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Parsing and status reporting for exchange credentials.

Error messages produced here may be returned to API clients, so they must
only ever reference field names, never credential values.
"""

import dataclasses
import typing as t

from threatexchange.exchanges import auth
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls
from threatexchange.utils import dataclass_json

from OpenMediaMatch.storage.interface import CredentialSource, IFlaskUnifiedStore

MAX_CREDENTIAL_VALUE_LENGTH = 8192


class CredentialValidationError(ValueError):
    """A credential payload was rejected. The message is safe to return."""


def supports_auth(api_cls: TSignalExchangeAPICls) -> bool:
    return issubclass(api_cls, auth.SignalExchangeWithAuth)


def parse_credential_json(
    api_cls: TSignalExchangeAPICls, raw: t.Any, *, require_valid: bool = True
) -> t.Optional[auth.CredentialHelper]:
    """
    Validate a credential_json payload against the API's credential dataclass.

    Returns None for null or {} (meaning "no credentials" / clear).
    If require_valid, also rejects credentials that fail the API's own
    format check (CredentialHelper._are_valid()).
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise CredentialValidationError("`credential_json` must be an object")
    if not raw:
        return None
    if not supports_auth(api_cls):
        raise CredentialValidationError(
            f"Exchange API '{api_cls.get_name()}' does not support credentials"
        )
    cred_cls = t.cast(t.Type[auth.SignalExchangeWithAuth], api_cls).get_credential_cls()
    if not dataclasses.is_dataclass(t.cast(t.Any, cred_cls)):
        raise CredentialValidationError(
            f"Exchange API '{api_cls.get_name()}' does not support setting "
            "credentials from json"
        )

    fields = {f.name: f for f in dataclasses.fields(cred_cls) if f.init}
    allowed = sorted(fields)
    if any(not isinstance(k, str) or k not in fields for k in raw):
        raise CredentialValidationError(
            f"`credential_json` has unexpected fields; allowed fields: {allowed}"
        )
    missing = sorted(
        name
        for name, f in fields.items()
        if name not in raw
        and f.default is dataclasses.MISSING
        and f.default_factory is dataclasses.MISSING
    )
    if missing:
        raise CredentialValidationError(
            f"`credential_json` is missing required fields: {missing}"
        )
    for name, val in raw.items():
        if val is None or isinstance(val, (bool, int, float)):
            # Type-checked against the dataclass when loading below
            continue
        if not isinstance(val, str):
            raise CredentialValidationError(
                f"`credential_json` field '{name}' must be a scalar value"
            )
        if len(val) > MAX_CREDENTIAL_VALUE_LENGTH:
            raise CredentialValidationError(
                f"`credential_json` field '{name}' is too long"
            )
        if "\x00" in val:
            raise CredentialValidationError(
                f"`credential_json` field '{name}' contains invalid characters"
            )

    try:
        creds = dataclass_json.dataclass_load_dict(raw, cred_cls)
        valid = creds._are_valid() or not require_valid
    except Exception:
        # The underlying exception message can include the offending value
        raise CredentialValidationError(
            f"`credential_json` is not valid for '{api_cls.get_name()}'"
        ) from None
    if not valid:
        raise CredentialValidationError(
            f"`credential_json` is not valid for '{api_cls.get_name()}'"
        )
    return creds


def credential_status(
    storage: IFlaskUnifiedStore, collab: CollaborationConfigBase
) -> t.Dict[str, t.Any]:
    """
    Describe which credentials an exchange will use, without any values.

    {
        "supports_auth": true,
        "has_credentials": true,
        "source": "exchange" | "api" | "environment" | "file" | null
    }
    """
    api_cls = storage.exchange_apis_get_installed().get(collab.api)
    if api_cls is None or not supports_auth(api_cls):
        return {"supports_auth": False, "has_credentials": False, "source": None}
    _, source = storage.exchange_get_resolved_credentials(collab)
    if source is None:
        cred_cls = t.cast(
            t.Type[auth.SignalExchangeWithAuth], api_cls
        ).get_credential_cls()
        source = _fallback_source(cred_cls)
    return {
        "supports_auth": True,
        "has_credentials": source is not None,
        "source": source,
    }


def _fallback_source(
    cred_cls: t.Type[auth.CredentialHelper],
) -> t.Optional[CredentialSource]:
    """Which CredentialHelper env/file fallback would supply valid credentials."""
    sources: t.List[
        t.Tuple[CredentialSource, t.Callable[[], t.Optional[auth.CredentialHelper]]]
    ] = [("environment", cred_cls._from_env), ("file", cred_cls._from_file)]
    for source, load in sources:
        try:
            creds = load()
        except Exception:
            # Same as CredentialHelper.get(): the first populated source wins,
            # even if it's malformed, so later sources won't be used
            return None
        if creds is not None:
            return source if creds._are_valid() else None
    return None
