# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Introspect exchange config and credential dataclasses to produce a
JSON-serializable schema for building dynamic forms (e.g. create exchange,
set credentials).
"""

import dataclasses
import typing as t
from dataclasses import MISSING
from enum import Enum


# Fields that are set by the UI (bank name, api type, enabled) and should
# not appear in the "type-specific" config schema for creating an exchange.
CONFIG_IGNORE_FIELDS = frozenset({"name", "api", "enabled"})


def _field_type_kind(field: dataclasses.Field) -> t.Tuple[str, t.Any]:
    """Return (kind, choices_or_none). kind is a string for the frontend."""
    typ = field.type
    origin = t.get_origin(typ)
    if isinstance(typ, type) and issubclass(typ, Enum):
        return "enum", [m.value for m in typ]
    if origin is not None:
        args = t.get_args(typ)
        # Optional[X] is Union[X, None]; X | None is UnionType in 3.10+
        if origin is t.Union or (getattr(t, "UnionType", None) and origin is getattr(t, "UnionType")):
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                sub_kind, sub_choices = _type_to_kind(non_none[0])
                return sub_kind, sub_choices
        if origin in (set, frozenset) and args:
            sub_kind, _ = _type_to_kind(args[0])
            return f"set_of_{sub_kind}", None
        if origin is list and args:
            sub_kind, _ = _type_to_kind(args[0])
            return f"list_of_{sub_kind}", None
    return _type_to_kind(typ)


def _type_to_kind(typ: t.Any) -> t.Tuple[str, t.Any]:
    if typ is type(None):
        return "string", None  # fallback
    if isinstance(typ, type) and issubclass(typ, Enum):
        return "enum", [m.value for m in typ]
    if typ is str or typ is t.Optional[str]:
        return "string", None
    if typ is int or typ is t.Optional[int]:
        return "number", None
    if typ is bool or typ is t.Optional[bool]:
        return "boolean", None
    if typ is float:
        return "number", None
    return "string", None  # safe fallback for unknown types


def _default_to_json(default: t.Any) -> t.Any:
    if default is MISSING:
        return None
    if isinstance(default, Enum):
        return default.value
    if isinstance(default, (set, frozenset)):
        return list(default)
    if isinstance(default, (list, tuple)):
        return [_default_to_json(x) for x in default]
    if dataclasses.is_dataclass(default) and not isinstance(default, type):
        return {f.name: _default_to_json(getattr(default, f.name)) for f in dataclasses.fields(default)}
    if isinstance(default, (str, int, float, bool)) or default is None:
        return default
    return str(default)  # fallback


def dataclass_field_descriptors(
    cls: t.Type[t.Any],
    *,
    ignore_fields: t.Optional[t.AbstractSet[str]] = None,
    only_init: bool = True,
) -> t.List[t.Dict[str, t.Any]]:
    """
    Introspect a dataclass and return a list of field descriptors suitable
    for building a form (e.g. JSON Schema–style or custom UI).

    Returns a list of dicts with keys:
      - name: str
      - type: str  ("string", "number", "boolean", "enum", "set_of_number", etc.)
      - required: bool
      - default: JSON-serializable value or None
      - help: str (from field.metadata["help"] or "")
      - choices: list of values for enum, else None
    """
    if not dataclasses.is_dataclass(cls):
        return []
    ignore = ignore_fields or frozenset()
    out: t.List[t.Dict[str, t.Any]] = []
    for f in dataclasses.fields(cls):
        if only_init and not f.init:
            continue
        if f.name in ignore:
            continue
        kind, choices = _field_type_kind(f)
        required = f.default is MISSING and f.default_factory is MISSING
        default = None
        if not required:
            if f.default_factory is not MISSING:
                try:
                    default = f.default_factory()
                    default = _default_to_json(default)
                except Exception:
                    default = None
            else:
                default = _default_to_json(f.default)
        help_text = (f.metadata.get("help") or "") if f.metadata else ""
        out.append({
            "name": f.name,
            "type": kind,
            "required": required,
            "default": default,
            "help": help_text,
            "choices": choices,
        })
    return out


def exchange_api_schema(
    api_cls: t.Type[t.Any],
    *,
    config_ignore_fields: t.AbstractSet[str] = CONFIG_IGNORE_FIELDS,
) -> t.Dict[str, t.Any]:
    """
    Build the full schema for an exchange API: config (type-specific fields
    for api_json) and optionally credentials.

    Returns:
      - config_schema: { "fields": [ ... ] }
      - credentials_schema: { "fields": [ ... ] } or None if API has no auth
    """
    config_cls = api_cls.get_config_cls()
    config_fields = dataclass_field_descriptors(
        config_cls,
        ignore_fields=config_ignore_fields,
        only_init=True,
    )
    result: t.Dict[str, t.Any] = {
        "config_schema": {"fields": config_fields},
        "credentials_schema": None,
    }
    if hasattr(api_cls, "get_credential_cls"):
        try:
            cred_cls = api_cls.get_credential_cls()  # type: ignore[attr-defined]
            cred_fields = dataclass_field_descriptors(
                cred_cls,
                ignore_fields=frozenset(),
                only_init=True,
            )
            result["credentials_schema"] = {"fields": cred_fields}
        except Exception:
            pass
    return result
