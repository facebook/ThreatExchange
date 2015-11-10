__PROXIES = None
__VERIFY = None


def get_proxies():
    """
    Returns the existing proxies setting.
    """

    global __PROXIES
    return __PROXIES


def get_verify():
    """
    Returns the existing verify setting.
    """

    global __VERIFY
    return __VERIFY


def connection(proxies=None, verify=None):
    """
    Configure proxies and verify settings for requests. This is a global setting
    that all requests calls will use unless overridden on a per-call basis.

    :param proxies: proxy info for requests.
    :type proxies: dict
    :param verify: verify info for requests.
    :type verify: bool, str
    """
    global __PROXIES
    global __VERIFY

    __PROXIES = proxies
    __VERIFY = verify
