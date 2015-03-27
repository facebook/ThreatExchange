import json
import requests

from errors import pytxFetchError
from vocabulary import ThreatExchange as t
from vocabulary import ThreatExchangeMember as tem

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

    def __init__(self, app_id=None, app_secret=None, **kwargs):
        if app_id and app_secret:
            self.setup(app_id, app_secret)
        for name, value in kwargs.items():
            self.__setattr__(name, value)

    def __setattr__(self, name, value):
        if name in self._fields or name in self._internal:
            object.__setattr__(self, name, value)

    def setup(self, app_id, app_secret):
        self._access_token = app_id + "|" + app_secret

    def _get_new(self, attrs):
        """
        Return a new instance of self.

        :param attrs: The attributes to set for this new instance.
        :type attrs: dict
        :returns: instance of self
        """

        n = self.__class__(**attrs)
        n._access_token = self._access_token
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
        d = dict(
            (n, getattr(self, n, None)) for n in self._fields
        )
        return d

