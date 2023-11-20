import re
import typing as t

from flask import Blueprint
from flask import request, jsonify, abort
from sqlalchemy.exc import IntegrityError
from threatexchange.signal_type.signal_base import SignalType
from werkzeug.exceptions import HTTPException

from OpenMediaMatch import persistence, utils
from OpenMediaMatch.storage.interface import BankConfig, SignalTypeIndexBuildCheckpoint
from OpenMediaMatch.blueprints import hashing
from OpenMediaMatch.storage.postgres import database


bp = Blueprint("curation", __name__)
bp.register_error_handler(HTTPException, utils.api_error_handler)

# Banking


@bp.route("/banks", methods=["GET"])
def banks_index():
    storage = persistence.get_storage()
    return list(storage.get_banks().values())


@bp.route("/bank/<bank_name>", methods=["GET"])
def bank_show_by_name(bank_name: str):
    storage = persistence.get_storage()

    bank = storage.get_bank(bank_name)
    if not bank:
        abort(404, f"bank '{bank_name}' not found")
    return jsonify(bank)


@bp.route("/banks", methods=["POST"])
def bank_create():
    name = utils.require_json_param("name")
    data = request.get_json()
    enabled_ratio = 1.0
    if "enabled_ratio" in data:
        enabled_ratio = utils.str_to_type(data["enabled_ratio"], float)
    elif "enabled" in data:
        enabled_ratio = 1.0 if utils.str_to_bool(data["enabled"]) else 0.0
    return jsonify(bank_create_impl(name, enabled_ratio)), 201


def bank_create_impl(name: str, enabled_ratio: float = 1.0) -> BankConfig:
    bank = BankConfig(name=name, matching_enabled_ratio=enabled_ratio)
    try:
        persistence.get_storage().bank_update(bank, create=True)
    except ValueError as e:
        abort(400, *e.args)
    except IntegrityError:
        abort(403, "Bank already exists")
    return bank


@bp.route("/bank/<bank_name>", methods=["PUT"])
def bank_update(bank_name: str):
    # TODO - rewrite using persistence.get_storage()
    storage = persistence.get_storage()
    data = request.get_json()
    bank = storage.get_bank(bank_name)
    rename_from: t.Optional[str] = None
    if bank is None:
        abort(404, "Bank not found")

    try:
        if "name" in data:
            rename_from = bank.name
            bank.name = data["name"]
        if "enabled" in data:
            bank.matching_enabled_ratio = 1 if bool(data["enabled"]) else 0
        if "enabled_ratio" in data:
            bank.matching_enabled_ratio = data["enabled_ratio"]

        storage.bank_update(bank, rename_from=rename_from)
    except ValueError as e:
        abort(400, *e.args)
    return jsonify(bank)


@bp.route("/bank/<bank_name>", methods=["DELETE"])
def bank_delete(bank_name: str):
    storage = persistence.get_storage()
    storage.bank_delete(bank_name)
    return {"message": "Done"}


@bp.route("/bank/<bank_name>/content", methods=["POST"])
def bank_add_file(bank_name: str):
    """
    Add content to a bank by providing a URI to the content (via the `url`
    query parameter), or uploading a file (via multipart/form-data).
    @see OpenMediaMatch.blueprints.hashing hash_media()
    @see OpenMediaMatch.blueprints.hashing hash_media_post()

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

    # Url was passed as a query param?
    if request.args.get("url", None):
        hashes = hashing.hash_media()
    # File uploaded via multipart/form-data?
    elif request.files:
        hashes = hashing.hash_media_post_impl()
    else:
        abort(400, "Neither `url` query param nor multipart file upload was received")
    return _bank_add_signals(bank, hashes)


def _bank_add_signals(
    bank: BankConfig, signal_type_to_signal_str: dict[str, str]
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
    content_id = storage.bank_add_content(
        bank.name,
        signals,
    )

    return {
        "id": content_id,
        "signals": {st.get_name(): val for st, val in signals.items()},
    }


@bp.route("/bank/<bank_name>/signal", methods=["POST"])
def bank_add_as_signals(bank_name: str):
    """
    Add a signal/hash directly to the bank.

    Most of the time you want to add by file, since you'll be able
    able to process the file in all of the techniques you have available.
    """
    storage = persistence.get_storage()
    bank = storage.get_bank(bank_name)
    if not bank:
        abort(404, f"bank '{bank_name}' not found")
    return _bank_add_signals(bank, t.cast(dict[str, str], request.json))


def _get_collab(name: str):
    storage = persistence.get_storage()
    collab = storage.get_collaboration(name)
    if collab is None:
        abort(404, f"Exchange '{name}' not found")
    return collab


# Fetching/Exchanges (aka collaborations)
@bp.route("/exchanges/apis", methods=["GET"])
def exchange_api_list() -> list[str]:
    exchange_apis = persistence.get_storage().get_exchange_type_configs()
    return list(exchange_apis)


@bp.route("/exchanges", methods=["POST"])
def exchange_create():
    """
    Creates an exchange configuration
    Inputs:
     * Configuration name in CAPS_AND_UNDERSCORE (must not be the same as an existing bank name)
     * Exchange type
     * Exchange-specific arguments (depends on SignalExchangeAPI)
    """
    data = request.get_json()
    name = utils.require_json_param("name")

    if not re.match("^[A-Z0-9_]+$", name):
        abort(400, "Field `name` must match /^[A-Z_]$/")

    if "type" not in data:
        abort(400, "Field `type` is required")

    if not isinstance(data.get("additional_config", {}), dict):
        abort(400, "Field `additional_config` must be object")

    exchange = database.CollaborationConfig(
        name=name,
        api_cls=data.get("type"),
        typed_config=data.get("additional_config", {}),
    )
    database.db.session.add(exchange)
    database.db.session.commit()
    return jsonify({"message": "Created successfully"}), 201


@bp.route("/exchanges", methods=["GET"])
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
    return [name for name in storage.get_collaborations()]


@bp.route("/exchange/<string:exchange_name>", methods=["GET"])
def exchange_show_by_name(exchange_name: str):
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
    return _get_collab(exchange_name)


@bp.route("/exchange/<string:exchange_name>/status")
def exchange_get_fetch_status(exchange_name: str):
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
    collab = _get_collab(exchange_name)
    abort(501, "Not yet implemented")


@bp.route("/exchange/<string:exchange_name>", methods=["PUT"])
def exchange_update(exchange_name: str):
    """
    Edit exchange configuration
    Inputs:
      * Configuration name
      * JSON serialization of configuration elements to update

    Returns:
      * JSON serialization of configuration, includes exchange-specific metadata

    {
      'name': 'FAKE_EXCHANGE',
      'api': 'fb_threatexchange',
      'enabled': true,
      ...
    }
    """
    collab = _get_collab(exchange_name)
    abort(501, "Not yet implemented")


@bp.route("/exchange/<string:exchange_name>", methods=["DELETE"])
def exchange_delete(exchange_name: str):
    """
    Delete exchange configuration
    Inputs:
     * Configuration name
     * (optional) whether to also delete the associated bank (defaults to true)

    Returns:
    {
      "message": "success",
    }
    """
    storage = persistence.get_storage()
    collab = storage.get_collaboration(exchange_name)
    if collab is None:
        return {"message": "success"}
    abort(501, "Not yet implemented")


# Signal Types
@bp.route("/signal_type", methods=["GET"])
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


@bp.route("/signal_type/<signal_type_name>", methods=["PUT"])
def update_signal_type_config(signal_type_name: str):
    """
    Update mutable fields of the signal type config

    Returns: The new value for the signal type config
    {
        "name": "pdq"
        "enabled_ratio": 1.0,
    }
    """
    enabled_ratio = utils.str_to_type(utils.require_json_param("enabled_ratio"), float)
    persistence.get_storage().create_or_update_signal_type_override(
        signal_type_name, enabled_ratio
    )
    return jsonify({"name": signal_type_name, "enabled_ratio": enabled_ratio}), 204


@bp.route("/signal_type/index", methods=["GET"])
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
            tar = SignalTypeIndexBuildCheckpoint.get_empty()
        if last is None:
            last = SignalTypeIndexBuildCheckpoint.get_empty()
        ret[name] = {
            "db_size": tar.total_hash_count,
            "index_size": last.total_hash_count,
            "index_out_of_date": last != tar,
            "newest_db_item": tar.last_item_timestamp,
            "index_built_to": last.last_item_timestamp,
        }
    return ret


# Content Types
@bp.route("/content_type", methods=["GET"])
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
