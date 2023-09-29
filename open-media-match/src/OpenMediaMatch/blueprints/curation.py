from flask import Blueprint
from flask import request, jsonify, abort

from OpenMediaMatch import database, persistence, utils


bp = Blueprint("curation", __name__)


@bp.route("/banks", methods=["GET"])
def banks_index():
    storage = persistence.get_storage()
    return list(storage.get_banks().values())


@bp.route("/bank/<bank_name>", methods=["GET"])
@utils.abort_to_json
def bank_show_by_name(bank_name: str):
    storage = persistence.get_storage()

    bank = storage.get_bank(bank_name)
    if not bank:
        utils.abort(404, f"bank '{bank_name}' not found")
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
