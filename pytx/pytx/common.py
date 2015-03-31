import json
import requests

import init

from vocabulary import Common as c
from vocabulary import Status as s
from vocabulary import ThreatExchange as t
from vocabulary import ThreatIndicator as ti
from errors import pytxFetchError, pytxValueError, pytxInitError

class Common(object):

    _internal = [
        '_DETAILS',
        '_RELATED',
        '_changed',
        '_new',
        '_access_token',
        c.ID
    ]

    _changed = []
    _new = True
    _access_token = None

    def __init__(self, **kwargs):
        self._access_token = init.__ACCESS_TOKEN__
        if self._access_token == None:
            raise pytxInitError("Must init() before instantiating")
        for name, value in kwargs.items():
            self.__setattr__(name, value)

    def __setattr__(self, name, value):
        if name in self._fields or name in self._internal:
            object.__setattr__(self, name, value)
            if name == c.ID:
                self._DETAILS = self._DETAILS + value + '/'
                self._RELATED = self._DETAILS + t.RELATED
            if name not in self._changed and name not in self._internal:
                self._changed.append(name)

    def set(self, name, value):
        self.__setattr__(name, value)

    def get(self, attr):
        self.__getattr__(attr)

    @property
    def access_token(self):
        """
        Returns the combined APP-ID and APP-SECRET.

        :returns: str
        """

        return self._access_token

    def to_dict(self):
        d = dict(
            (n, getattr(self, n, None)) for n in self._fields
        )
        return d

    def _get_new(self, attrs):
        """
        Return a new instance of self.

        :param attrs: The attributes to set for this new instance.
        :type attrs: dict
        :returns: instance of self
        """

        n = self.__class__(**attrs)
        n._new = False
        return n

    def _is_timestamp(self, timestamp):
        """
        Verifies the timestamp provided is a valid timestamp.

        :param timestamp: Value to verify is a timestamp.
        :type timestamp: str
        :returns: True if valid, :class:`pytxValueError` if invalid.
        """

        try:
            int(timestamp)
            return True
        except ValueError, e:
            raise pytxValueError(e)

    def _validate_limit(self, limit):
        """
        Verifies the limit provided is valid and within the max limit Facebook
        will allow you to use (currently 5000).

        :param limit: Value to verify is a valid limit.
        :type limit: int, str
        :returns: :class:`pytxValueError` if invalid.
        """

        try:
            int(limit)
        except ValueError, e:
            raise pytxValueError(e)
        if limit > t.MAX_LIMIT:
            raise pytxValueError(
                "limit cannot exceed %s (default: %s)" % (t.MAX_LIMIT,
                                                          t.DEFAULT_LIMIT)
            )
        return

    def _validate_get(self, limit, since, until):
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
            self._is_timestamp(since)
        if until:
            self._is_timestamp(until)
        if limit:
            self._validate_limit(limit)

    def _sanitize_strict(self, strict_text):
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

    def _build_get_parameters(self, text=None, strict_text=None, type_=None,
                             limit=None, since=None, until=None):
        """
        Validate arguments and convert them into GET parameters.

        :param text: The text used for limiting the search.
        :type text: str
        :param strict_text: Whether we should use strict searching.
        :type strict_text: bool, str, int
        :param type_: The Indicator type to limit to.
        :type type_: str
        :param limit: The maximum number of objects to return.
        :type limit: int, str
        :param since: The timestamp to limit the beginning of the search.
        :type since: str
        :param until: The timestamp to limit the end of the search.
        :type until: str
        :returns: dict
        """

        self._validate_get(limit, since, until)
        strict = self._sanitize_strict(strict_text)
        params = {}
        if text:
            params[t.TEXT] = text
        if strict is not None:
            params[t.STRICT_TEXT] = strict
        if type_:
            params[t.TYPE] = type_
        if limit:
            params[t.LIMIT] = limit
        if since:
            params[t.SINCE] = since
        if until:
            params[t.UNTIL] = until
        return params

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
        return self._handle_results(resp)


    def _post(self, url, params={}):
        """
        Send the POST request.

        :param url: The URL to send the POST request to.
        :type url: str
        :param params: The POST parameters to send in the request.
        :type params: dict
        :returns: dict (using json.loads())
        """

        params[t.ACCESS_TOKEN] = self._access_token
        resp = requests.post(url, params=params)
        return self._handle_results(resp)

    def _delete(self, url, params={}):
        """
        Send the DELETE request.

        :param url: The URL to send the DELETE request to.
        :type url: str
        :param params: The DELETE parameters to send in the request.
        :type params: dict
        :returns: dict (using json.loads())
        """

        params[t.ACCESS_TOKEN] = self._access_token
        resp = requests.delete(url, params=params)
        return self._handle_results(resp)

    def _get_generator(self, url, total, params={}):
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
        :param params: The GET parameters to send in the request.
        :type params: dict
        :returns: Generator
        """

        if total is None:
            total = t.NO_TOTAL
        if total == t.MIN_TOTAL:
            yield None
        next_ = True
        while next_:
            results = self._get(url, params)
            for data in results[t.DATA]:
                if total == t.MIN_TOTAL:
                    raise StopIteration
                yield self._get_new(data)
                total -= t.DEC_TOTAL
            try:
                next_ = results[t.PAGING][t.NEXT]
            except:
                next_ = False
            if next_:
                url = next_
                params = {}

    def objects(self, text=None, strict_text=False, type_=None,
                limit=None, since=None, until=None):
        """
        Get objects from the ThreatExchange.

        :param text: The text used for limiting the search.
        :type text: str
        :param strict_text: Whether we should use strict searching.
        :type strict_text: bool, str, int
        :param type_: The Indicator type to limit to.
        :type type_: str
        :param limit: The maximum number of objects to return.
        :type limit: int, str
        :param since: The timestamp to limit the beginning of the search.
        :type since: str
        :param until: The timestamp to limit the end of the search.
        :type until: str
        :returns: Generator
        """

        params = self._build_get_parameters(
            text=text,
            strict_text=strict_text,
            type_=type_,
            limit=limit,
            since=since,
            until=until,
        )
        return self._get_generator(self._URL, limit, params=params)

    def details(self, fields=None, connection=None):
        """
        Get object details. Allows you to limit the fields returned in the
        object's details. Also allows you to provide a connection. If a
        connection is provided, the related objects will be returned instead
        of the object itself.

        :param fields: The fields to limit the details to.
        :type fields: None, str, list
        :param connection: The connection to find other related objects with.
        :type connection: None, str
        :returns: ???
        """

        if connection:
            url = self._DETAILS + connection + '/'
        else:
            url = self._DETAILS
        params = self._build_get_parameters()
        if isinstance(fields, basestring):
            fields = fields.split(',')
        if fields is not None and not isinstance(fields, list):
            raise pytxValueError("fields must be a list")
        if fields is not None:
            params[t.FIELDS] = ','.join(f.strip() for f in fields)
        if connection:
            return self._get_generator(url, t.NO_TOTAL, params=params)
        else:
            return self._get_new(self._get(url, params=params))

    def save(self, url):
        """
        Save this object. If it is a new object, use self._fields to build the
        POST and submit to the appropriate URL. If it is an update to an
        existing object, use self._changed to only submit the modified
        attributes in the POST.

        :returns: dict (using json.loads())
        """

        if self._new:
            params = dict(
                (n, getattr(self, n)) for n in self._fields if n != c.ID
            )
            return self._post(self._URL, params=params)
        else:
            params = dict(
                (n, getattr(self, n)) for n in self._changed if n != c.ID
            )
            return self._post(self._DETAILS, params=params)

    def expire(self, timestamp):
        """
        Expire by setting the 'expired_on' timestamp.

        :param timestamp: The timestamp to set for an expiration date.
        :type timestamp: str
        """

        self._is_timestamp(timestamp)
        self.set(ti.EXPIRED_ON, timestamp)
        self.save()

    def false_positive(self, object_id):
        """
        Mark an object as a false positive by setting the status to
        NON_MALICIOUS.

        :param object_id: The object-id of the object to mark.
        :type object_id: str
        """

        self.set(c.STATUS, s.NON_MALICIOUS)
        self.save()

    def add_connection(self, object_id):
        """
        Use HTTP POST and add a connection between two objects.

        :param object_id: The other object-id in the connection.
        :type object_id: str
        :returns: dict (using json.loads())
        """

        params = {
            t.RELATED_ID: object_id
        }
        return self._post(self._RELATED, params=params)

    # DELETE REQUESTS

    def delete_connection(self, object_id):
        """
        Use HTTP DELETE and remove the connection to another object.

        :param object_id: The other object-id in the connection.
        :type object_id: str
        :returns: dict (using json.loads())
        """

        params = {
            t.RELATED_ID: object_id
        }
        return self._delete(self._RELATED, params=params)
