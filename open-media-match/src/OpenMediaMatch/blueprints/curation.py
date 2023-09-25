from flask import Blueprint
from flask import request, current_app, jsonify

from OpenMediaMatch import database


bp = Blueprint("curation", __name__)


@bp.route("/banks", methods=["GET"])
def banks_index():
    banks = (
        database.db.session.execute(current_app.db.select(database.Bank))
        .scalars()
        .all()
    )
    return jsonify(banks)


@bp.route("/bank/<int:bank_id>", methods=["GET"])
def bank_show_by_id(bank_id: int):
    bank = database.Bank.query.get(bank_id)
    if not bank:
        return jsonify({"message": "bank not found"}), 404
    return jsonify(bank)


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
