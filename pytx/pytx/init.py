import os

from errors import pytxInitError
from request import Broker as b
from vocabulary import ThreatExchange as te


__ACCESS_TOKEN__ = None
Broker = None


def init(app_id=None, app_secret=None, token_file=None):
    """
    Use the app_id and app_secret to store the access_token globally for all
    instantiated objects to leverage.

    If you use token_file, you can either:
        - put the app_id and app_token on separate lines
        - combine them with a "|" in between on a single line

    If no options are passed into this function, it will check for the following
    environment variables:
        - TX_APP_ID
        - TX_APP_SECRET
        - TX_ACCESS_TOKEN

    The latter is the combined app_id and app_secret with a "|" in between.

    :param app_id: The APP-ID to use.
    :type app_id: str
    :param app_secret: The APP-SECRET to use.
    :type app_secret: str
    :param token_file: The full path and filename where to find the access token.
    :type token_file: str
    :raises: :class:`errors.pytxIniterror`
    """

    global __ACCESS_TOKEN__
    global Broker

    if app_id and app_secret:
        try:
            __ACCESS_TOKEN__ = app_id + "|" + app_secret
        except Exception, e:
            raise pytxInitError("Error generating access token: %s" % str(e))
    elif token_file:
        try:
            with open(token_file, 'r') as infile:
                token_list = []
                for line in infile:
                    token_list.append(line.strip())
                if len(token_list) == 1:
                    __ACCESS_TOKEN__ = token_list[0]
                elif len(token_list) == 2:
                    __ACCESS_TOKEN__ = token_list[0] + "|" + token_list[1]
                else:
                    raise pytxInitError(
                        "Error generating access token from file: %s" % token_file
                    )
        except Exception, e:
            raise pytxInitError(str(e))
    else:
        access_token = os.environ.get(te.TX_ACCESS_TOKEN, None)
        if access_token is None:
            app_id = os.environ.get(te.TX_APP_ID, None)
            app_secret = os.environ.get(te.TX_APP_SECRET, None)
            if app_id is None or app_secret is None:
                raise pytxInitError(
                    "Environment variables not set."
                )
            else:
                access_token = app_id.strip() + "|" + app_secret.strip()
        __ACCESS_TOKEN__ = access_token.strip()
    Broker = b()
    return
