from flask import Blueprint
from flask import abort, request

bp = Blueprint("hashing", __name__)

@bp.route('/hash')
def hash_media():
    """
    Fetch content and return its hash.
    TODO: implement
    """
    media_url = request.args.get('url', None)
    if media_url is None:
        # path is required, otherwise we don't know what we're hashing.
        # TODO: a more helpful message
        abort(400)
    
    hash_types = request.args.get('types', None)
    if hash_types is not None:
        # TODO: parse this into a list of hash types
        pass


    # TODO
    #  - download the media
    #  - decode it
    #  - hash it
    
