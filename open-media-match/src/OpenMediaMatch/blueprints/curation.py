from flask import Blueprint
from flask import request, jsonify

from OpenMediaMatch import database
from OpenMediaMatch.utils import abort_to_json

import re

bp = Blueprint("curation", __name__)

# Todo
#  - Clean up the way we return responses
#  - Type-annotate all functions

# Fetching/Exchanges
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

    if not "name" in data:
        return jsonify({"message": "Field `name` is required"}), 400
    name = str(data.get("name"))
    if not re.match("^[A-Z_]+$", name):
        return jsonify({"message": "Field `name` must match /^[A-Z_]$/"}), 400
    
    if not "type" in data:
        return jsonify({"message": "Field `type` is required"}), 400
        
    if type(data.get("additional_config", {})) != dict:
        return jsonify({"message": "Field `additional_config` must be object"}), 400
    
    exchange = database.Exchange(
        name=name,
        type=data.get("type"),
        fetching_enabled=bool(data.get("fetching_enabled", True)),
        seen_enabled=bool(data.get("seen_enabled", True)),
        report_true_positive=bool(data.get("report_true_positive", True)),
        report_false_positive=bool(data.get("report_false_positive", True)),
        additional_config=data.get("additional_config", {})
    )
    database.db.session.add(exchange)
    database.db.session.commit()
    return jsonify({"message": "Created successfully"}), 201


@bp.route("/exchanges", methods=["GET"])
def exchanges_index():
    """
    List all exchange configurations
    Output:
     * List of all exchange configuration names
    """
    return jsonify({"message": "unimplemented"}), 501


@bp.route("/exchange/<string:exchange>", methods=["GET"])
def exchange_show_by_name(exchange: str):
    """
    Gets a single exchange configuration by name
    Inputs:
     * Exchange configuration name
    Output:
     * JSON serialization of configuration, includes exchange-specific metadata
    """
    return jsonify({"message": "unimplemented"}), 501


@bp.route("/exchange/<string:exchange>/status")
def exchange_get_fetch_status(exchange: str):
    """
    Inputs:
     * Configuration name
    Outputs:
     * Time of last fetch in unix time
     * Time of checkpoint in unix time
     * Whether the last run resulted in an error
    """
    return jsonify({"message": "unimplemented"}), 501


@bp.route("/exchange/<string:exchange>", methods=["PUT"])
def exchange_update(exchange: str):
    """
    Edit exchange configuration
    Inputs:
     * Configuration name
     * JSON serialization of configuration elements to update
    """
    return jsonify({"message": "unimplemented"}), 501


@bp.route("/exchange/<string:exchange>", methods=["DELETE"])
def exchange_delete(exchange: str):
    """
    Delete exchange configuration
    Inputs:
     * Configuration name
     * (optional) whether to also delete the associated bank (defaults to true)
    """
    return jsonify({"message": "unimplemented"}), 501


# Bank management

@bp.route("/banks", methods=["GET"])
def banks_index():
    banks = [
        b.as_storage_iface_cls()
        for b in database.db.session.execute(database.db.select(database.Bank))
        .scalars()
        .all()
    ]
    return jsonify(banks)


@bp.route("/bank/<bank_name>", methods=["GET"])
def bank_show_by_name(bank_name: str):
    bank = (
        database.db.session.execute(
            database.db.select(database.Bank).where(database.Bank.name == bank_name)
        )
        .scalars()
        .all()
    )
    return jsonify(bank)


@bp.route("/banks", methods=["POST"])
def bank_create():
    data = request.get_json()
    if not "name" in data:
        return jsonify({"message": "Field `name` is required"}), 400
    bank = database.Bank(name=data["name"], enabled=bool(data.get("enabled", True)))
    database.db.session.add(bank)
    database.db.session.commit()
    return jsonify({"message": "Created successfully"}), 201


@bp.route("/bank/<int:bank_id>", methods=["PUT"])
def bank_update(bank_id: int):
    data = request.get_json()
    bank = database.Bank.query.get(bank_id)
    if not bank:
        return jsonify({"message": "bank not found"}), 404

    if "name" in data:
        bank.name = data["name"]
    if "enabled" in data:
        bank.enabled = bool(data["enabled"])

    database.db.session.commit()
    return jsonify(bank)


@bp.route("/bank/<int:bank_id>", methods=["DELETE"])
def bank_delete(bank_id: int):
    bank = database.Bank.query.get(bank_id)
    if not bank:
        return jsonify({"message": "bank not found"}), 404
    database.db.session.delete(bank)
    database.db.session.commit()
    return jsonify({"message": f"Bank {bank.name} ({bank.id}) deleted"})
