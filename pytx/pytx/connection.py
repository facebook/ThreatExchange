__PROXIES = None
__VERIFY = None
__HEADERS = None


def get_headers():
    """
    Returns the existing headers setting.
    """

    global __HEADERS
    return __HEADERS


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


def connection(headers=None, proxies=None, verify=None):
    """
    Configure headers, proxies, and verify settings for requests. This is a
    global setting that all requests calls will use unless overridden on a
    per-call basis.

    :param headers: header info for requests.
    :type headers: dict
    :param proxies: proxy info for requests.
    :type proxies: dict
    :param verify: verify info for requests.
    :type verify: bool, str
    """
    global __HEADERS
    global __PROXIES
    global __VERIFY

    __HEADERS = headers
    __PROXIES = proxies
    __VERIFY = verify
