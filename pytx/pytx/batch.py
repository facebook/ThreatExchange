import json

from access_token import get_access_token
from request import Broker

from vocabulary import Batch as b
from vocabulary import ThreatExchange as t
from errors import (
    pytxFetchError
)


class Batch(object):

    """
    Class for making Batch requests to the API.
    """

    def __init__(self, **kwargs):
        """
        Initialized the object.
        """

    @classmethod
    def get_relative(cls, url):
        """
         Parse the full URL to get the relative URL.
        """

        return url.replace(t.URL, '')

    @classmethod
    def submit(cls,
               *args,
               **kwargs):
        """
        Submit batch request. All non-named args are considered to be
        dictionaries containing the following:

            type: The request type (GET, POST, etc.).
            url: The full or relative URL for the API call.
            body: If the type is POST this is the body that will be used.

        All named args are considered to be the options below.

        :param include_headers: Include headers in response.
        :type include_headers: bool
        :param retries: Number of retries before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: dict (using json.loads())
        """

        batch = []
        for arg in args:
            d = {b.METHOD: arg.get('type', 'GET'),
                 b.RELATIVE_URL: Batch.get_relative(arg.get('url', ''))}
            body = arg.get('body', None)
            if body:
                d[b.BODY] = body
            batch.append(d)
            include_headers = Broker.sanitize_bool(kwargs.get('include_headers',
                                                              'false'))
        params = {t.ACCESS_TOKEN: get_access_token(),
                  t.BATCH: json.dumps(batch),
                  t.INCLUDE_HEADERS: include_headers}
        try:
            retries = kwargs.get('retries', None)
            headers = kwargs.get('headers', None)
            proxies = kwargs.get('proxies', None)
            verify = kwargs.get('verify', None)

            return Broker.post(t.URL,
                               params=params,
                               retries=retries,
                               headers=headers,
                               proxies=proxies,
                               verify=verify)
        except:
            raise pytxFetchError('Error with batch request.')
