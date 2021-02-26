from flask import Blueprint, request, jsonify

matcher_api = Blueprint('matcher_api', __name__)

@matcher_api.route('/query', methods=['GET', 'POST'])
def matcher_query():
    if request.method == 'POST':
        hashes = request.json['hashes']
        matches = [ hash for hash in hashes if _mock_is_index_match(hash)]
        return jsonify({
            "matched_hashes": matches,
            "unmatched_hashes": [hash for hash in hashes if hash not in matches]
        })
    else:
        hash = request.args.get('hash')
        if _mock_is_index_match(hash):
            return ('', 200)
        else:
            return ('', 404)

# Replace this with actual index lookup
import random
def _mock_is_index_match(hash: str):
    return bool(random.getrandbits(1))
