import json

from .access_token import get_access_token
from .request import Broker

from .vocabulary import Batch as b
from .vocabulary import ThreatExchange as t
from .errors import (
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
    def prepare_single_request(cls, request, name=None):
        """
        Prepare a single request to be included in batch.

        :param request: A dictionary in the format required by Batch.submit().
        :type request: dict
        :param name: A name to give this request.
        :type name: str
        :returns: dict
        """

        d = {b.METHOD: request.get('type',
                                   request.get('method', 'GET')),
             b.RELATIVE_URL: Batch.get_relative(request.get('url',
                                                            request.get('relative_url', '')))}
        body = request.get('body', None)
        if body:
            d[b.BODY] = body
        if name:
            d['name'] = name
        return d

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

        If you use "method" instead of "type" and/or "relative_urL" instead of
        "url" (which is accurate to the Graph API) we will use them
        appropriately.

        If you pass a named argument, we will consider the name as the name you
        wish to include in that specific request. This is useful for referencing
        a request in another request in the Batch (see FB documentation).

        The following named args are considered to be the options below.

        :param include_headers: Include headers in response.
        :type include_headers: bool
        :param omit_response: Omit response on success.
        :type omit_response: bool
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
        retries = kwargs.get('retries', None)
        if retries:
            del kwargs['retries']
        headers = kwargs.get('headers', None)
        if headers:
            del kwargs['headers']
        proxies = kwargs.get('proxies', None)
        if proxies:
            del kwargs['proxies']
        verify = kwargs.get('verify', None)
        if verify:
            del kwargs['verify']
        include_headers = kwargs.get('include_headers', None)
        if include_headers:
            del kwargs['include_headers']
            include_headers = Broker.sanitize_bool(include_headers)
        omit_response = kwargs.get('omit_response', None)
        if omit_response:
            del kwargs['omit_response']
            omit_response = Broker.sanitize_bool(omit_response)

        for arg in args:
            batch.append(Batch.prepare_single_request(arg))
        for key, value in kwargs.iteritems():
            batch.append(Batch.prepare_single_request(value, name=key))
        params = {t.ACCESS_TOKEN: get_access_token(),
                  t.BATCH: json.dumps(batch),
                  t.INCLUDE_HEADERS: include_headers,
                  t.OMIT_RESPONSE_ON_SUCCESS: omit_response}
        try:
            return Broker.post(t.URL,
                               params=params,
                               retries=retries,
                               headers=headers,
                               proxies=proxies,
                               verify=verify)
        except:
            raise pytxFetchError('Error with batch request.')
