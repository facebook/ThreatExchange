import json
import requests

from access_token import get_access_token

from vocabulary import ThreatExchange as t
from errors import (
    pytxFetchError,
    pytxValueError
)


class Broker(object):

    """
    The Broker handles validation and submission of requests as well as
    consumption and returning of the result. It is leveraged by the other
    classes.

    Since the Broker takes care of the entire request/response cycle, it can be
    used on its own to interact with the ThreatExchange API without the need for
    the other classes if a developer wishes to use it.
    """

    @staticmethod
    def get_new(klass, attrs):
        """
        Return a new instance of klass.

        :param klass: The class to create a new instance of.
        :type klass: :class:
        :param attrs: The attributes to set for this new instance.
        :type attrs: dict
        :returns: new instance of klass
        """

        n = klass(**attrs)
        n._new = False
        return n

    @staticmethod
    def is_timestamp(timestamp):
        """
        Verifies the timestamp provided is a valid timestamp.

        Valid timestamps are based on PHP's "strtotime" function. As of right
        now even with python's "dateutil" library there are some strtotime valid
        strings that do not validate properly. Until such a time as this can
        become accurate and robust enough to have feature parity with strtotime,
        this will always return True and leave proper timestamps to the API
        user.

        :param timestamp: Value to verify is a timestamp.
        :type timestamp: str
        :returns: True
        """

        return True

    @staticmethod
    def validate_limit(limit):
        """
        Verifies the limit provided is valid and within the max limit Facebook
        will allow you to use.

        :param limit: Value to verify is a valid limit.
        :type limit: int, str
        :returns: :class:`pytxValueError` if invalid.
        """

        try:
            int(limit)
        except ValueError, e:
            raise pytxValueError(e)
        return

    @staticmethod
    def sanitize_strict(strict_text):
        """
        If strict_text is provided, sanitize it.

        'true' will be used if strict_text is in [True, 'true', 'True', 1].
        'false' will be used if strict_text is in [False, 'false', 'False', 0].

        If we receive any other value strict_text will be set to None and
        ignored when building the GET request.

        :param strict_text: The value to sanitize.
        :type strict_text: bool, str, int
        :returns: str, None
        """

        if strict_text in (True, 'true', 'True', 1):
            strict = 'true'
        elif strict_text in (False, 'false', 'False', 0):
            strict = 'false'
        else:
            strict = None
        return strict

    @staticmethod
    def handle_results(resp):
        """
        Handle the results of a request.

        :param resp: The HTTP response.
        :type resp: response object
        :returns: dict (using json.loads())
        """

        if resp.status_code != 200:
            raise pytxFetchError('Response code: %s: %s' % (resp.status_code,
                                                            resp.text))
        try:
            results = json.loads(resp.text)
        except:
            raise pytxFetchError('Unable to convert response to JSON.')
        return results

    @classmethod
    def validate_get(cls, limit, since, until):
        """
        Executes validation for the GET parameters: limit, since, until.

        :param limit: The limit to validate.
        :type limit: int, str
        :param since: The since timestamp to validate.
        :type since: str
        :param until: The until timestamp to validate.
        :type until: str
        """

        if since:
            cls.is_timestamp(since)
        if until:
            cls.is_timestamp(until)
        if limit:
            cls.validate_limit(limit)

    @classmethod
    def build_get_parameters(cls, text=None, strict_text=None, type_=None, threat_type=None,
                             fields=None, limit=None, since=None, until=None):
        """
        Validate arguments and convert them into GET parameters.

        :param text: The text used for limiting the search.
        :type text: str
        :param strict_text: Whether we should use strict searching.
        :type strict_text: bool, str, int
        :param type_: The Indicator type to limit to.
        :type type_: str
        :param threat_type: The Threat type to limit to.
        :type threat_type: str
        :param fields: Select specific fields to pull
        :type fields: str, list
        :param limit: The maximum number of objects to return.
        :type limit: int, str
        :param since: The timestamp to limit the beginning of the search.
        :type since: str
        :param until: The timestamp to limit the end of the search.
        :type until: str
        :returns: dict
        """

        cls.validate_get(limit, since, until)
        strict = cls.sanitize_strict(strict_text)
        params = {}
        if text:
            params[t.TEXT] = text
        if strict is not None:
            params[t.STRICT_TEXT] = strict
        if type_:
            params[t.TYPE] = type_
        if threat_type:
            params[t.THREAT_TYPE] = threat_type
        if fields:
            params[t.FIELDS] = ','.join(fields) if isinstance(fields, list) else fields
        if limit:
            params[t.LIMIT] = limit
        if since:
            params[t.SINCE] = since
        if until:
            params[t.UNTIL] = until
        return params

    @classmethod
    def get(cls, url, params=None):
        """
        Send a GET request.

        :param url: The URL to send the GET request to.
        :type url: str
        :param params: The GET parameters to send in the request.
        :type params: dict
        :returns: dict (using json.loads())
        """
        if not params:
            params = dict()

        params[t.ACCESS_TOKEN] = get_access_token()
        resp = requests.get(url, params=params)
        return cls.handle_results(resp)

    @classmethod
    def post(cls, url, params=None):
        """
        Send a POST request.

        :param url: The URL to send the POST request to.
        :type url: str
        :param params: The POST parameters to send in the request.
        :type params: dict
        :returns: dict (using json.loads())
        """

        if not params:
            params = dict()

        params[t.ACCESS_TOKEN] = get_access_token()
        resp = requests.post(url, params=params)
        return cls.handle_results(resp)

    @classmethod
    def delete(cls, url, params=None):
        """
        Send a DELETE request.

        :param url: The URL to send the DELETE request to.
        :type url: str
        :param params: The DELETE parameters to send in the request.
        :type params: dict
        :returns: dict (using json.loads())
        """

        if not params:
            params = dict()

        params[t.ACCESS_TOKEN] = get_access_token()
        resp = requests.delete(url, params=params)
        return cls.handle_results(resp)

    @classmethod
    def get_generator(cls, klass, url, total, to_dict=False, params=None):
        """
        Generator for managing GET requests. For each GET request it will yield
        the next object in the results until there are no more objects. If the
        GET response contains a 'next' value in the 'paging' section, the
        generator will automatically fetch the next set of results and continue
        the process until the total limit has been reached or there is no longer
        a 'next' value.

        :param url: The URL to send the GET request to.
        :type url: str
        :param total: The total number of objects to return (-1 to disable).
        :type total: None, int
        :param to_dict: Return a dictionary instead of an instantiated class.
        :type to_dict: bool
        :param params: The GET parameters to send in the request.
        :type params: dict
        :returns: Generator
        """

        if not params:
            params = dict()

        if total is None:
            total = t.NO_TOTAL
        if total == t.MIN_TOTAL:
            yield None
        next_ = True
        while next_:
            results = cls.get(url, params)
            for data in results[t.DATA]:
                if total == t.MIN_TOTAL:
                    raise StopIteration
                if to_dict:
                    yield data
                else:
                    yield cls.get_new(klass, data)
                total -= t.DEC_TOTAL
            try:
                next_ = results[t.PAGING][t.NEXT]
            except:
                next_ = False
            if next_:
                url = next_
                params = {}
