import os

from .errors import pytxAccessTokenError
from .vocabulary import ThreatExchange as te


__ACCESS_TOKEN = None
# File level global


def _read_token_file(token_file):
    """
    Read a token file. Separated out for easy mocking during unit testing.

    :param token_file: The full path and filename where to find the access token.
    :type token_file: str
    :returns: str
    :raises: :class:`errors.pytxAccessTokenError`
    """
    try:
        with open(token_file, 'r') as infile:
            return infile.readline().strip()
    except IOError as e:
        raise pytxAccessTokenError(str(e))


def get_access_token():
    """
    Returns the existing access token if access_token() has been called.
    Will attempt to access_token() in the case that there is no access token.

    :raises: :class:`errors.pytxAccessTokenError` if there is no access token.
    """
    global __ACCESS_TOKEN

    if not __ACCESS_TOKEN:
        access_token()

    if not __ACCESS_TOKEN:
        raise pytxAccessTokenError('Must access_token() before instantiating')

    return __ACCESS_TOKEN


def get_app_id():
    """
    Returns the app_id.
    """

    token = get_access_token()
    try:
        return token.split('|')[0]
    except:
        raise pytxAccessTokenError('Could not derive app-id from token')


def _find_token_file():
    for loc in [os.curdir, os.path.expanduser('~')]:
        filepath = os.path.join(loc, '.pytx')
        if os.path.exists(filepath):
            return filepath

    return None


def access_token(app_id=None, app_secret=None, token_file=None):
    """
    Use the app_id and app_secret to store the access_token globally for all
    instantiated objects to leverage.

    There are many ways to specify the app_id and app_secret. In order, we will try:
     1. Use the value of the 'TX_ACCESS_TOKEN' environment variable.
     2. Use the concatenation of the 'TX_APP_ID' and 'TX_APP_SECRET' environment variables.
     3. Use the first line of the file '$PWD/.pytx' or ~/.pytx'
     4. Use the concatenation of the app_id and app_secret parameters
     5. Use the first line of the file 'token_file'

    :param app_id: The APP-ID to use.
    :type app_id: str
    :param app_secret: The APP-SECRET to use.
    :type app_secret: str
    :param token_file: The full path and filename where to find the access token.
    :type token_file: str
    :raises: :class:`errors.pytxAccessTokenError`
    """
    global __ACCESS_TOKEN

    # 1. Use the concatenation of the app_id and app_secret parameters
    if app_id and app_secret:
        __ACCESS_TOKEN = app_id + '|' + app_secret
        return

    # 2. Use the value of the 'TX_ACCESS_TOKEN' environment variable.
    __ACCESS_TOKEN = os.environ.get(te.TX_ACCESS_TOKEN, None)
    if __ACCESS_TOKEN:
        return

    # 3. Use the concatenation of the 'TX_APP_ID' and 'TX_APP_SECRET' environment variables.
    env_app_id = os.environ.get(te.TX_APP_ID, None)
    env_app_secret = os.environ.get(te.TX_APP_SECRET, None)
    if env_app_id and env_app_secret:
        __ACCESS_TOKEN = env_app_id + '|' + env_app_secret
        return

    # 4. Use the first line of the file '$PWD/.pytx' or ~/.pytx'
    filepath = _find_token_file()
    if filepath:
        __ACCESS_TOKEN = _read_token_file(filepath)
        return

    # 5. Use the first line of the file 'token_file'
    if token_file:
        __ACCESS_TOKEN = _read_token_file(token_file)
        return

    raise pytxAccessTokenError('Unable to set access token.')
