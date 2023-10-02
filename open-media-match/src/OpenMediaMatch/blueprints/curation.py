from flask import Blueprint
from flask import request, jsonify, abort

from threatexchange.signal_type.pdq.signal import PdqSignal

from OpenMediaMatch import database, persistence, utils
from OpenMediaMatch.storage.interface import BankConfig


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
    persistence.get_storage().bank_update(bank, create=True)
    return jsonify(bank), 201


@bp.route("/bank/<int:bank_id>", methods=["PUT"])
def bank_update(bank_id: int):
    # TODO - rewrite using persistence.get_storage()
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
    # TODO - rewrite using persistence.get_storage()
    bank = database.Bank.query.get(bank_id)
    if not bank:
        return jsonify({"message": "bank not found"}), 404
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
    # TODO
    storage = persistence.get_storage()
    bank = storage.get_bank(bank_name)
    if not bank:
        abort(404, f"bank '{bank_name}' not found")

    return {
        "id": 1234,
        "signals": {
            PdqSignal.get_name(): PdqSignal.get_examples()[0],
        },
        "message": "TODO: this is a fake implementation!",
    }
