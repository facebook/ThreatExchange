import json
import requests

import init

from vocabulary import ThreatExchange as t
from vocabulary import ThreatExchangeMember as tem
from errors import (
    pytxFetchError,
    pytxAttributeError,
    pytxInitError
)

class ThreatExchangeMember(object):

    _URL = t.URL + t.THREAT_EXCHANGE_MEMBERS

    _internal = [
        '_access_token',
    ]

    _fields = [
        tem.ID,
        tem.NAME
    ]

    _access_token = None

    def __init__(self, **kwargs):
        """
        Initialize the object. Set the _access_token and any attributes that
        were provided.
        """

        self._access_token = init.__ACCESS_TOKEN__
        if self._access_token == None:
            raise pytxInitError("Must init() before instantiating")
        for name, value in kwargs.items():
            self.__setattr__(name, value)

    def __getattr__(self, attr):
        """
        Get an attribute. If the attribute does not exist, return None
        """

        if attr not in self._fields and attr not in self._internal:
            raise pytxAttributeError("%s is not a valid attribute" % attr)

        try:
            return object.__getattribute__(self, attr)
        except:
            return None

    def get(self, attr):
        """
        Wrapper around __getattr__ making it easier to use the vocabulary to get
        class attributes.

        :param attr: The name of the attribute to get.
        :type attr: str
        """

        return self.__getattr__(attr)

    def _get_new(self, attrs):
        """
        Return a new instance of self.

        :param attrs: The attributes to set for this new instance.
        :type attrs: dict
        :returns: instance of self
        """

        n = self.__class__(**attrs)
        return n

    def _handle_results(self, resp):
        """
        Handle the results of a request.

        :param resp: The HTTP response.
        :type resp: response object
        :returns: dict (using json.loads())
        """

        if resp.status_code != 200:
            raise pytxFetchError("Response code: %s" % resp.status_code)
        try:
            results = json.loads(resp.text)
        except:
            raise pytxFetchError("Unable to convert response to JSON.")
        return results

    def _get(self, url, params={}):
        """
        Send the GET request.

        :param url: The URL to send the GET request to.
        :type url: str
        :param params: The GET parameters to send in the request.
        :type params: dict
        :returns: dict (using json.loads())
        """

        params[t.ACCESS_TOKEN] = self._access_token
        resp = requests.get(url, params=params)
        members = self._handle_results(resp).get(t.DATA, [])
        total = len(members)
        if total == t.MIN_TOTAL:
            yield None
        else:
            for member in members:
                yield self._get_new(member)

    def objects(self):
        """
        Get a list of Threat Exchange Members

        :returns: dict
        """

        return self._get(self._URL)

    def to_dict(self):
        """
        Convert this object into a dictionary.

        :returns: dict
        """

        d = dict(
            (n, getattr(self, n, None)) for n in self._fields
        )
        return d

