import re

from flask import Blueprint
from flask import request, jsonify, abort

from sqlalchemy.exc import IntegrityError

from threatexchange.signal_type.pdq.signal import PdqSignal

from OpenMediaMatch import database, persistence, utils
from OpenMediaMatch.storage.interface import BankConfig
from OpenMediaMatch.blueprints.hashing import hash_media


bp = Blueprint("curation", __name__)

# Banking


@bp.route("/banks", methods=["GET"])
@utils.abort_to_json
def banks_index():
    storage = persistence.get_storage()
    return list(storage.get_banks().values())


@bp.route("/bank/<bank_name>", methods=["GET"])
@utils.abort_to_json
def bank_show_by_name(bank_name: str):
    storage = persistence.get_storage()

    bank = storage.get_bank(bank_name)
    if not bank:
        abort(404, f"bank '{bank_name}' not found")
    return jsonify(bank)


@bp.route("/banks", methods=["POST"])
@utils.abort_to_json
def bank_create():
    name = utils.require_json_param("name")
    data = request.get_json()
    enabled_ratio = 1.0
    if "enabled_ratio" in data:
        enabled_ratio = utils.str_to_type(data["enabled_ratio"], float)
    elif "enabled" in data:
        enabled_ratio = 1.0 if utils.str_to_bool(data["enabled"]) else 0.0

    bank = BankConfig(name=name, matching_enabled_ratio=enabled_ratio)
    try:
        persistence.get_storage().bank_update(bank, create=True)
    except ValueError as e:
        abort(400, *e.args)
    except IntegrityError:
        abort(403, "Bank already exists")
    return jsonify(bank), 201


@bp.route("/bank/<bank_name>", methods=["PUT"])
@utils.abort_to_json
def bank_update(bank_name: str):
    # TODO - rewrite using persistence.get_storage()
    data = request.get_json()
    bank = database.Bank.query.filter_by(name=bank_name).one_or_none()
    if bank is None:
        abort(404, "Bank not found")

    try:
        if "name" in data:
            bank.name = data["name"]
        if "enabled" in data:
            bank.enabled = bool(data["enabled"])

        database.db.session.commit()
    except ValueError as e:
        abort(400, *e.args)
    return jsonify(bank.as_storage_iface_cls())


@bp.route("/bank/<bank_name>", methods=["DELETE"])
@utils.abort_to_json
def bank_delete(bank_name: str):
    # TODO - rewrite using persistence.get_storage()
    bank = database.Bank.query.filter_by(name=bank_name).one_or_none()
    if not bank:
        return {"message": "Done"}, 200
    database.db.session.delete(bank)
    database.db.session.commit()
    return jsonify({"message": f"Bank {bank.name} ({bank.id}) deleted"})


@bp.route("/bank/<bank_name>/content", methods=["POST"])
@utils.abort_to_json
def bank_add_by_url(bank_name: str):
    """
    Add content to a bank by providing a URI to the content.
    @see OpenMediaMatch.blueprints.hashing hash_media()

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

    hashes = hash_media()

    signal_type_configs = storage.get_signal_type_configs()

    content_id = storage.bank_add_content(
        bank.name,
        {
            signal_type_configs[name].signal_type: signal_value
            for name, signal_value in hashes.items()
        },
    )

    return {"id": content_id, "signals": hashes}


def _get_collab(name: str):
    storage = persistence.get_storage()
    collab = storage.get_collaboration(name)
    if collab is None:
        abort(404, f"Exchange '{name}' not found")
    return collab


# Fetching/Exchanges (aka collaborations)
@bp.route("/exchanges", methods=["POST"])
@utils.abort_to_json
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

    if not re.match("^[A-Z_]+$", name):
        abort(400, "Field `name` must match /^[A-Z_]$/")

    if "type" not in data:
        abort(400, "Field `type` is required")

    if not isinstance(data.get("additional_config", {}), dict):
        abort(400, "Field `additional_config` must be object")

    exchange = database.Exchange(
        name=name,
        type=data.get("type"),
        fetching_enabled=bool(data.get("fetching_enabled", True)),
        seen_enabled=bool(data.get("seen_enabled", True)),
        report_true_positive=bool(data.get("report_true_positive", True)),
        report_false_positive=bool(data.get("report_false_positive", True)),
        additional_config=data.get("additional_config", {}),
    )
    database.db.session.add(exchange)
    database.db.session.commit()
    return jsonify({"message": "Created successfully"}), 201


@bp.route("/exchanges", methods=["GET"])
def exchanges_index():
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
@utils.abort_to_json
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
@utils.abort_to_json
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
@utils.abort_to_json
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
@utils.abort_to_json
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
        "enabled": true,
        "name": "pdq"
      },
      {
        "enabled": true,
        "name": "video_md5"
      }
    ]
    """
    return [
        {"name": c.signal_type.get_name(), "enabled": c.enabled}
        for c in persistence.get_storage().get_signal_type_configs().values()
    ]


@bp.route("/signal_type/<signal_type_name>", methods=["PUT"])
@utils.abort_to_json
def update_signal_type_config(signal_type_name: str):
    """
    Update mutable fields of the signal type config

    Returns: The new value for the signal type config
    {
        "name": "pdq"
        "enabled": true,
    }
    """
    abort(501, "unimplemented")


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
@utils.abort_to_json
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
