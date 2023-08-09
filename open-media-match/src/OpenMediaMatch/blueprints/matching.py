from flask import Blueprint
from flask import abort, request

bp = Blueprint("matching", __name__)

# TODO: everything :D

@bp.route('/lookup')
def lookup():
    """
    Look up a hash in the similarity index
    Input:
     * Signal type (hash type)
     * Signal value (the hash)
     * Optional list of banks to restrict search to
    Output:
     * List of matching content items
    """
    abort(501) # Unimplemented
 
@bp.route('/index/status')
def index_status():
    """
    Input:
     * Signal type (hash type)
    Output:
     * Time of last index build
    """
    abort(501) # Unimplemented