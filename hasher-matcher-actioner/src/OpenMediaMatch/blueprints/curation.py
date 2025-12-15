# Copyright (c) Meta Platforms, Inc. and affiliates.

import re
import time
import typing as t
from datetime import datetime, timedelta

from flask_openapi3 import APIBlueprint
from flask_openapi3.models import Tag
from flask import Response, abort, jsonify, request
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from threatexchange.utils import dataclass_json
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.exchanges import auth

from OpenMediaMatch import persistence
from OpenMediaMatch.utils import flask_utils
import OpenMediaMatch.storage.interface as iface
from OpenMediaMatch.blueprints import hashing
from OpenMediaMatch.schemas.curation import (
    BankConfig,
    BankContentResponse,
    BankCreateRequest,
    BankUpdateRequest,
    BankedContentMetadata,
    ExchangeConfig,
    ExchangeUpdateRequest,
)
from OpenMediaMatch.schemas.shared import ErrorResponse, SuccessResponse


def five_years_from_now() -> int:
    return int(time.mktime((datetime.now() + timedelta(days=365 * 5)).timetuple()))


bp = APIBlueprint("curation", __name__, url_prefix="/c")
bp.register_error_handler(HTTPException, flask_utils.api_error_handler)

# Banking


class BankPathParams(BaseModel):
    bank_name: str


class BankContentPathParams(BankPathParams):
    content_id: int


class ExchangePathParams(BaseModel):
    exchange_name: str


@bp.get(
    "/banks",
    tags=[Tag(name="Banks")],
    responses={"200": {"description": "List of banks"}},
    summary="List banks",
    description="Get list of all banks",
)
def banks_index():
    storage = persistence.get_storage()
    return list(storage.get_banks().values())


@bp.get(
    "/bank/<bank_name>",
    tags=[Tag(name="Banks")],
    responses={"200": BankConfig, "404": ErrorResponse},
    summary="Get bank",
    description="Get bank configuration by name",
)
def bank_show_by_name(path: BankPathParams):
    bank_name = path.bank_name
    storage = persistence.get_storage()

    bank = storage.get_bank(bank_name)
    if not bank:
        abort(404, f"bank '{bank_name}' not found")
    return jsonify(bank)


@bp.post(
    "/banks",
    tags=[Tag(name="Banks")],
    responses={"201": BankConfig, "400": ErrorResponse, "403": ErrorResponse},
    summary="Create bank",
    description="Create a new bank",
)
def bank_create(body: BankCreateRequest):
    if body.enabled_ratio is not None:
        enabled_ratio = body.enabled_ratio
    elif body.enabled is not None:
        enabled_ratio = 1.0 if body.enabled else 0.0
    else:
        enabled_ratio = 1.0
    return jsonify(bank_create_impl(body.name, enabled_ratio)), 201


def bank_create_impl(name: str, enabled_ratio: float = 1.0) -> iface.BankConfig:
    bank = iface.BankConfig(name=name, matching_enabled_ratio=enabled_ratio)
    try:
        persistence.get_storage().bank_update(bank, create=True)
    except ValueError as e:
        abort(400, *e.args)
    except IntegrityError:
        abort(403, "Bank already exists")
    return bank


@bp.put(
    "/bank/<bank_name>",
    tags=[Tag(name="Banks")],
    responses={
        "200": BankConfig,
        "400": ErrorResponse,
        "403": ErrorResponse,
        "404": ErrorResponse,
    },
    summary="Update bank",
    description="Update bank configuration",
)
def bank_update(path: BankPathParams, body: BankUpdateRequest):
    bank_name = path.bank_name
    storage = persistence.get_storage()
    bank = storage.get_bank(bank_name)
    rename_from: t.Optional[str] = None
    if bank is None:
        abort(404, "Bank not found")

    try:
        if body.name is not None:
            rename_from = bank.name
            bank.name = body.name
        if body.enabled is not None:
            bank.matching_enabled_ratio = 1 if bool(body.enabled) else 0
        if body.enabled_ratio is not None:
            bank.matching_enabled_ratio = body.enabled_ratio

        storage.bank_update(bank, rename_from=rename_from)
    except ValueError as e:
        abort(400, *e.args)
    except IntegrityError:
        abort(403, "Bank name already exists")
    return jsonify(bank)


@bp.delete(
    "/bank/<bank_name>",
    tags=[Tag(name="Banks")],
    responses={"200": SuccessResponse, "404": ErrorResponse},
    summary="Delete bank",
    description="Delete a bank",
)
def bank_delete(path: BankPathParams):
    bank_name = path.bank_name
    storage = persistence.get_storage()
    storage.bank_delete(bank_name)
    return {"message": "Done"}


def _validate_bank_add_metadata() -> t.Optional[BankedContentMetadata]:
    if not request.is_json:
        print("Not json")
        return None
    j = request.json
    print("json: %s" % j)
    if not isinstance(j, dict):
        print("Not dict")
        return None
    metadata = j.get("metadata")
    if metadata is None:
        print("Not meta")
        return None
    # Validate
    if not isinstance(metadata, dict):
        abort(400, "metadata should be a json object")

    try:
        return BankedContentMetadata(**metadata)
    except ValidationError as e:
        abort(400, f"Invalid metadata: {str(e)}")


@bp.get(
    "/bank/<bank_name>/content/<int:content_id>",
    tags=[Tag(name="Bank Content")],
    responses={"200": BankContentResponse, "404": ErrorResponse},
    summary="Get bank content",
    description="Get details of a specific content item in a bank",
)
def bank_get_content(path: BankContentPathParams):
    bank_name = path.bank_name
    content_id = path.content_id
    storage = persistence.get_storage()
    bank = storage.get_bank(bank_name)
    if not bank:
        abort(404, f"bank '{bank_name}' not found")
    include_signals = request.args.get("include_signals", "false").lower() == "true"
    content = storage.bank_content_get([content_id])
    if not content:
        abort(404, f"content '{content_id}' not found")
    content_config = content[0]

    collab_metadata = {
        key: list(values) for key, values in content_config.collab_metadata.items()
    }
    bank_schema = BankConfig(
        name=content_config.bank.name,
        matching_enabled_ratio=content_config.bank.matching_enabled_ratio,
    )
    signals_payload: t.Optional[dict[str, str]] = None
    if include_signals:
        signals = storage.bank_content_get_signals([content_id])
        if content_id in signals:
            signals_payload = dict(signals[content_id])

    response = BankContentResponse(
        id=content_config.id,
        disable_until_ts=content_config.disable_until_ts,
        collab_metadata=collab_metadata,
        original_media_uri=content_config.original_media_uri,
        bank=bank_schema,
        signals=signals_payload,
    )

    content_response = response.model_dump()
    if signals_payload is None:
        content_response.pop("signals", None)

    return jsonify(content_response)


@bp.post(
    "/bank/<bank_name>/content",
    tags=[Tag(name="Bank Content")],
    responses={"201": BankContentResponse, "400": ErrorResponse, "404": ErrorResponse},
    summary="Add content to bank",
    description="Add content to a bank by URL or file upload with optional metadata",
)
def bank_add_content(path: BankPathParams):
    bank_name = path.bank_name
    """
    Add content to a bank by providing a URI to the content (via the `url`
    query parameter), or uploading a file (via multipart/form-data).

    @see OpenMediaMatch.blueprints.hashing hash_media()
    @see OpenMediaMatch.blueprints.hashing hash_media_from_form_data()

    Inputs:
     * The content to be banked, in one of these formats:
        1. URI via the `url` query parameter
        2. form-data with the proper MIME type set
     * Optional metadata about the file in the `metadata` query param as a
       json object. All keys are optional:
       {
        content_id:  as a string, assumed (but not enforced) to be unique
        content_uri: as a URI. This WILL NOT be automatically populated from
                     the `url` parameter without being populated, and is
                     intended to be used for the
        json:        as a json object, can be anything you plan to need in
                     the long term
       }

    Returns: the signatures created and id

    {
      'id': 1234,
      'signals': {
         'pdq': 'facefacefacefacefacefaceface',
         'vmd5': 'ecafecafecafecafecafecafecaf'
         ...
      }
    }
    """
    storage = persistence.get_storage()
    bank = storage.get_bank(bank_name)
    if not bank:
        abort(404, f"bank '{bank_name}' not found")

    metadata = _validate_bank_add_metadata()

    url = request.args.get("url")

    # Url was passed as a query param?
    if url:
        hashes = hashing.hash_url_content(
            url,
            content_type_hint=request.args.get("content_type"),
            signal_type_names=request.args.get("types"),
        )
    # File uploaded via multipart/form-data?
    elif request.files:
        hashes = hashing.hash_media_from_form_data()
    else:
        abort(400, "Neither `url` nor multipart file upload was received")
    return _bank_add_signals(bank, hashes, metadata)


def _bank_add_signals(
    bank: iface.BankConfig,
    signal_type_to_signal_str: dict[str, str],
    metadata: t.Optional[BankedContentMetadata],
) -> dict[str, t.Any]:
    if not signal_type_to_signal_str:
        abort(400, "No signals given")

    storage = persistence.get_storage()

    signals: dict[type[SignalType], str] = {}
    signal_type_cfgs = storage.get_signal_type_configs()
    for name, val in signal_type_to_signal_str.items():
        st = signal_type_cfgs.get(name)
        if st is None:
            abort(400, f"No such signal type {name}")
        try:
            signals[st.signal_type] = st.signal_type.validate_signal_str(val)
        except Exception as e:
            abort(400, f"Invalid {name} signal: {str(e)}")

    content_config = iface.BankContentConfig(
        id=0,
        disable_until_ts=iface.BankContentConfig.ENABLED,
        collab_metadata={},
        original_media_uri=None,
        bank=bank,
    )

    content_id = storage.bank_add_content(bank.name, signals, content_config)

    return {
        "id": content_id,
        "signals": {st.get_name(): val for st, val in signals.items()},
    }


@bp.put(
    "/bank/<bank_name>/content/<int:content_id>",
    tags=[Tag(name="Bank Content")],
    responses={"200": SuccessResponse, "400": ErrorResponse, "404": ErrorResponse},
    summary="Update bank content",
    description="Update metadata for a specific content item in a bank",
)
def bank_update_content(path: BankContentPathParams):
    bank_name = path.bank_name
    content_id = path.content_id
    """
    Update the metadata for a banked content item.

    Inputs:
        * disable_until_ts (optional): Unix timestamp in seconds.
    """
    storage = persistence.get_storage()
    bank = storage.get_bank(bank_name)
    if not bank:
        abort(404, f"bank '{bank_name}' not found")
    contents = storage.bank_content_get([content_id])
    if not contents:
        abort(404, f"content '{content_id}' not found")
    content = contents[0]
    data = request.get_json()

    try:
        if "disable_until_ts" in data:
            disable_until_ts = flask_utils.str_to_type(data["disable_until_ts"], int)
            if disable_until_ts < 0:
                abort(400, "disable_until_ts must be a non-negative integer")
            if disable_until_ts > five_years_from_now():
                abort(400, "disable_until_ts must be less than 5 years in the future")
            content.disable_until_ts = disable_until_ts
        storage.bank_content_update(content)
    except KeyError as e:
        abort(404, *e.args)
    return jsonify(content)


@bp.delete(
    "/bank/<bank_name>/content/<int:content_id>",
    tags=[Tag(name="Bank Content")],
    responses={"200": SuccessResponse, "404": ErrorResponse},
    summary="Delete bank content",
    description="Remove a content item from a bank",
)
def bank_delete_content(path: BankContentPathParams):
    bank_name = path.bank_name
    content_id = path.content_id
    """
    Remove a signal from a bank.
    """
    storage = persistence.get_storage()
    bank = storage.get_bank(bank_name)
    if not bank:
        abort(404, f"bank '{bank_name}' not found")

    count = storage.bank_remove_content(bank.name, content_id)
    return {"deleted": count}


@bp.post(
    "/bank/<bank_name>/signal",
    tags=[Tag(name="Bank Content")],
    responses={"201": SuccessResponse, "400": ErrorResponse, "404": ErrorResponse},
    summary="Add signals to bank",
    description="Add content to bank by providing signal hashes directly",
)
def bank_add_as_signals(path: BankPathParams):
    bank_name = path.bank_name
    """
    Add a signal/hash directly to the bank.

    Most of the time you want to add by file, since you'll be able
    able to process the file in all of the techniques you have available.
    """
    storage = persistence.get_storage()
    bank = storage.get_bank(bank_name)
    if not bank:
        abort(404, f"bank '{bank_name}' not found")
    return _bank_add_signals(bank, t.cast(dict[str, str], request.json), None)


def _get_collab(name: str):
    storage = persistence.get_storage()
    collab = storage.exchange_get(name)
    if collab is None:
        abort(404, f"Exchange '{name}' not found")
    return collab


# Fetching/Exchanges (aka collaborations)
@bp.get(
    "/exchanges/apis",
    tags=[Tag(name="Exchanges")],
    responses={"200": {"description": "List of exchange API types"}},
    summary="List exchange API types",
    description="Get list of available exchange API types that can be configured",
)
def exchange_api_list() -> list[str]:
    exchange_apis = persistence.get_storage().exchange_apis_get_configs()
    return list(exchange_apis)


@bp.route("/exchanges/api/<string:api_name>", methods=["GET", "POST"])
def exchange_api_config_get_or_update(api_name: str) -> dict[str, t.Any]:
    storage = persistence.get_storage()
    api_cfg = storage.exchange_apis_get_configs().get(api_name)
    if api_cfg is None:
        abort(400, f"no such Exchange API '{api_name}'")

    if request.method == "POST":
        raw_json = request.json
        if not isinstance(raw_json, dict):
            abort(400, "this endpoint expects a json object payload")
        cred_json = raw_json.get("credential_json")
        if cred_json is not None:
            if not cred_json:
                api_cfg.credentials = None
            else:
                api_cfg.set_credentials_from_json_dict(cred_json)

        storage.exchange_api_config_update(api_cfg)

    return {
        "supports_authentification": issubclass(
            api_cfg.api_cls, auth.SignalExchangeWithAuth
        ),
        "has_set_authentification": api_cfg.credentials is not None,
    }


@bp.post(
    "/exchanges",
    tags=[Tag(name="Exchanges")],
    responses={"201": SuccessResponse, "400": ErrorResponse},
    summary="Create exchange",
    description="Create a new signal exchange configuration for collaborative sharing",
)
def exchange_create():
    """
    Creates an exchange configuration
    Inputs:
     * Configuration name in CAPS_AND_UNDERSCORE (must not be the same as an existing bank name)
     * Exchange type
     * Exchange-specific arguments (depends on SignalExchangeAPI)
    """
    data = request.get_json()
    bank = flask_utils.require_json_param("bank")
    api_json = data.get("api_json", {})
    api_type_name = data.get("api")

    if not re.match("^[A-Z0-9_]+$", bank):
        abort(400, "Field `bank` must match /^[A-Z0-9_]+$/")

    if not isinstance(api_json, dict):
        abort(400, "Field `api_json` must be object")

    storage = persistence.get_storage()
    api_types = storage.exchange_apis_get_installed()

    if api_type_name is None:
        abort(400, "Field `api_type` is required")
    if api_type_name not in api_types:
        abort(400, f"No such exchange type '{api_type_name}'")
    api_type = api_types[api_type_name]

    # Rehydrate our dict with the expected fields
    api_json["name"] = bank
    api_json.setdefault("enabled", True)
    api_json["api"] = api_type_name

    try:
        cfg = dataclass_json.dataclass_load_dict(api_json, api_type.get_config_cls())
    except Exception as e:
        abort(
            400,
            f"Failed to parse `api_json` - verify all fields are supplied. {str(e)}",
        )

    storage.exchange_update(cfg, create=True)

    return {"message": "Created successfully"}, 201


@bp.get(
    "/exchanges",
    tags=[Tag(name="Exchanges")],
    responses={"200": {"description": "List of exchange names"}},
    summary="List exchanges",
    description="Get list of all configured signal exchanges",
)
def exchange_list():
    """
    List all exchange configurations

    Returns: List of all exchange configuration names

    [
        "FAKE_EXCHANGE_1",
        "FAKE_EXCHANGE_2"
    ]
    """
    storage = persistence.get_storage()
    return [name for name in storage.exchanges_get()]


@bp.get(
    "/exchange/<string:exchange_name>",
    tags=[Tag(name="Exchanges")],
    responses={"200": ExchangeConfig, "404": ErrorResponse},
    summary="Get exchange",
    description="Get details of a specific exchange configuration",
)
def exchange_show_by_name(path: ExchangePathParams):
    """
    Gets a single exchange configuration by name
    Inputs:
      * Exchange configuration name
    Returns:
      * JSON serialization of configuration, includes exchange-specific metadata

    {
      'name': 'FAKE_EXCHANGE',
      'api': 'fb_threatexchange',
      'enabled': 1,
      ...
    }
    """
    # Workaround for serializing enums and sets. The smarter way would be to
    # override the root level json serializer, but that's a future project
    return Response(
        response=dataclass_json.dataclass_dumps(_get_collab(path.exchange_name)),
        status=200,
        mimetype="application/json",
    )


@bp.route("/exchange/<string:exchange_name>/status")
def exchange_get_fetch_status(path: ExchangePathParams):
    """
    Inputs:
      * Configuration name
    Return:
      * Time of last fetch kicked off in unix time (or 0 if unset)
      * Time of checkpoint in unix time (or 0 if unset)
      * Whether the last run resulted in an error

    {
        last_fetch_time: 1692397383,
        checkpoint_time: 169239700,
        success: true
    }
    """
    return jsonify(
        persistence.get_storage().exchange_get_fetch_status(
            _get_collab(path.exchange_name).name
        )
    )


@bp.put(
    "/exchange/<string:exchange_name>",
    tags=[Tag(name="Exchanges")],
    responses={"200": SuccessResponse, "400": ErrorResponse, "404": ErrorResponse},
    summary="Update exchange",
    description="Update an existing exchange configuration",
)
def exchange_update(path: ExchangePathParams, body: ExchangeUpdateRequest):
    """
    Edit exchange configuration

    Inputs:
      * Configuration name
      * enabled: bool

      At some point in the future may support more fields

    Returns:
      * JSON serialization of configuration, includes exchange-specific metadata

    {
      'name': 'FAKE_EXCHANGE',
      'api': 'fb_threatexchange',
      'enabled': true,
      ...
    }
    """
    collab = _get_collab(path.exchange_name)
    if body.enabled is not None:
        collab.enabled = body.enabled
    persistence.get_storage().exchange_update(collab, create=False)
    return Response(
        response=dataclass_json.dataclass_dump_dict(collab),
        status=200,
        mimetype="application/json",
    )


@bp.delete(
    "/exchange/<string:exchange_name>",
    tags=[Tag(name="Exchanges")],
    responses={"200": SuccessResponse, "404": ErrorResponse},
    summary="Delete exchange",
    description="Remove an exchange configuration",
)
def exchange_delete(path: ExchangePathParams):
    """
    Delete exchange configuration

    Inputs:
     * Exchange name

    Returns:
    {
      "message": "Exchange deleted",
    }
    """
    storage = persistence.get_storage()
    storage.exchange_delete(path.exchange_name)
    return {"message": "Exchange deleted"}


# Signal Types
@bp.get(
    "/signal_type",
    tags=[Tag(name="Configuration")],
    responses={"200": {"description": "List of signal type configurations"}},
    summary="List signal types",
    description="Get list of all signal types with their configuration",
)
def get_all_signal_types():
    """
    Lists all the signal type configs

    Returns: A list of all SignalType configs
    [
      {
        "enabled_ratio": 1.0,
        "name": "pdq"
      },
      {
        "enabled_ratio": 0.0,
        "name": "video_md5"
      }
    ]
    """
    return [
        {"name": c.signal_type.get_name(), "enabled_ratio": c.enabled_ratio}
        for c in persistence.get_storage().get_signal_type_configs().values()
    ]


@bp.put(
    "/signal_type/<signal_type_name>",
    tags=[Tag(name="Configuration")],
    responses={"200": SuccessResponse, "400": ErrorResponse, "404": ErrorResponse},
    summary="Update signal type",
    description="Update configuration for a specific signal type",
)
def update_signal_type_config(signal_type_name: str):
    """
    Update mutable fields of the signal type config

    Returns: The new value for the signal type config
    {
        "name": "pdq"
        "enabled_ratio": 1.0,
    }
    """
    enabled_ratio = flask_utils.str_to_type(
        flask_utils.require_json_param("enabled_ratio"), float
    )
    persistence.get_storage().create_or_update_signal_type_override(
        signal_type_name, enabled_ratio
    )
    return jsonify({"name": signal_type_name, "enabled_ratio": enabled_ratio}), 204


@bp.get(
    "/signal_type/index",
    tags=[Tag(name="Configuration")],
    responses={"200": {"description": "Index status for all signal types"}},
    summary="Signal type index status",
    description="Get the index build status for all signal types",
)
def signal_type_index_status() -> dict[str, dict[str, t.Any]]:
    """
    Get the index status for signal types.

    Example return: The new value for the signal type config
    {
        "db_size": 153,
        "index_size": 150,
        "index_out_of_date": true,
        "newest_db_item": 1700236661,
        "index_built_to": 1700236641,
    }
    """
    storage = persistence.get_storage()
    signal_types = storage.get_signal_type_configs()
    signal_type = request.args.get("signal_type")
    if signal_type is not None:
        if signal_type not in signal_types:
            abort(400, f"No such signal type '{signal_type}'")
        signal_types = {signal_type: signal_types[signal_type]}

    ret = {}
    for name, config in signal_types.items():
        last = storage.get_last_index_build_checkpoint(
            config.signal_type,
        )
        tar = storage.get_current_index_build_target(
            config.signal_type,
        )
        if tar is None:
            tar = iface.SignalTypeIndexBuildCheckpoint.get_empty()
        if last is None:
            last = iface.SignalTypeIndexBuildCheckpoint.get_empty()
        ret[name] = {
            "db_size": tar.total_hash_count,
            "index_size": last.total_hash_count,
            "index_out_of_date": last != tar,
            "newest_db_item": tar.last_item_timestamp,
            "index_built_to": last.last_item_timestamp,
        }
    return ret


# Content Types
@bp.get(
    "/content_type",
    tags=[Tag(name="Configuration")],
    responses={"200": {"description": "List of content type configurations"}},
    summary="List content types",
    description="Get list of all content types with their configuration",
)
def get_all_content_types():
    """
    Lists all the signal type configs

    Returns: A list of all SignalType configs
    [
        {
            "enabled": true,
            "name": "photo"
        },
        {
            "enabled": true,
            "name": "video"
        }
    ]
    """
    return [
        {"name": c.content_type.get_name(), "enabled": c.enabled}
        for c in persistence.get_storage().get_content_type_configs().values()
    ]


@bp.route("/signal_type/<signal_type_name>", methods=["PUT"])
def update_content_type_config(signal_type_name: str):
    """
    Update mutable fields of the content type config

    Returns: The new value for the signal type config
    {
        "name": "pdq"
        "enabled": true,
    }
    """
    abort(501, "unimplemented")
