from errors import pytxValueError


__ACCESS_TOKEN__ = None


def init(app_id=None, app_secret=None):
    global __ACCESS_TOKEN__
    if app_id and app_secret:
        __ACCESS_TOKEN__ = app_id + "|" + app_secret
    else:
        raise pytxValueError("Must provide an app_id and app_secret")
    return
