import json
import requests


class pytxValueError(Exception):
    """
    Exception for when we are given a value we are not expecting or is invalid.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class pytxFetchError(Exception):
    """
    Exception for when a GET or POST attempt fails.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class pytx(object):
    """
    Main class for interfacing with ThreatExchange.
    """

    _URL                        = 'https://graph.facebook.com/'

    # GET
    _MALWARE_ANALYSES           = 'malware_analyses'
    _THREAT_EXCHANGE_MEMBERS    = 'threat_exchange_members'
    _THREAT_INDICATORS          = 'threat_indicators'

    #POST

    def __init__(self, app_id, app_secret):
        """
        Setup initial access token. Combine them properly for the developer.

        :param app_id: Facebook APP-ID (provided by Facebook)
        :type app_id: str
        :param app_secret: Facebook APP-SECRET (provided by Facebook)
        :type app_secret: str
        """

        self._access_token = app_id + "|" + app_secret

    @property
    def url(self):
        """
        Provides the main URL where all requests will go.

        :returns: str
        """

        return self._URL

    @property
    def access_token(self):
        """
        Returns the combined APP-ID and APP-SECRET.

        :returns: str
        """

        return self._access_token

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
        if limit > 5000:
            raise pytxValueError("limit cannot exceed 5000 (default: 500)")
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

    def _get_strict(self, strict_text):
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
        strict = self._get_strict(strict_text)
        params = {
            'access_token': self._access_token,
        }
        if text:
            params['text'] = text
        if strict is not None:
            params['strict_text'] = strict
        if type_:
            params['type'] = type_
        if limit:
            params['limit'] = limit
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        return params

    def _fetch(self, url, params={}):
        """
        Send the GET request.

        :param url: The URL to send the GET request to.
        :type url: str
        :param params: The GET parameters to send in the request.
        :type params: dict
        :returns: dict (using json.loads())
        """

        resp = requests.get(url, params=params)
        if resp.status_code != 200:
            raise pytxFetchError("Response code: %s" % resp.status_code)
        try:
            results = json.loads(resp.text)
        except:
            raise pytxFetchError("Unable to convert response to JSON.")
        return results

    def _fetch_generator(self, url, total, params={}):
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
            total = -1
        if total == 0:
            yield None
        next_ = True
        while next_:
            results = self._fetch(url, params)
            for data in results['data']:
                if total == 0:
                    raise StopIteration
                yield data
                total -= 1
            try:
                next_ = results['paging']['next']
            except:
                next_ = False
            if next_:
                url = next_
                params = {}

    # GET REQUESTS

    def get_object(self, url, params={}):
        """
        Get the details for a single object.

        :param url: The URL to send the GET request to.
        :type url: str
        :param params: The GET parameters to send in the request.
        :type params: dict
        :returns: dict (using json.loads())
        """

        result = self._fetch(url, params)
        return result

    def malware_analyses(self, text, strict_text=False, limit=None,
                         since=None, until=None):
        """
        Get objects from Malware Analyses.

        :param text: The text used for limiting the search.
        :type text: str
        :param strict_text: Whether we should use strict searching.
        :type strict_text: bool, str, int
        :param limit: The maximum number of objects to return.
        :type limit: int, str
        :param since: The timestamp to limit the beginning of the search.
        :type since: str
        :param until: The timestamp to limit the end of the search.
        :type until: str
        :returns: Generator
        """

        url = self._URL + self._MALWARE_ANALYSES + '/'
        params = self._build_get_parameters(
            text=text,
            strict_text=strict_text,
            limit=limit,
            since=since,
            until=until
        )
        return self._fetch_generator(url, limit, params=params)

    def threat_exchange_members(self):
        """
        Get a list of Threat Exchange Members.

        :returns: Generator
        """

        url = self._URL + self._THREAT_EXCHANGE_MEMBERS + '/'
        params = self._build_get_parameters()
        return self._fetch_generator(url, -1, params=params)

    def threat_indicators(self, text, strict_text=False, type_=None,
                          limit=None, since=None, until=None):
        """
        Get objects from Threat Indicators.

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

        url = self._URL + self._THREAT_INDICATORS + '/'
        params = self._build_get_parameters(
            text=text,
            strict_text=strict_text,
            limit=limit,
            since=since,
            until=until,
            type_=type_
        )
        return self._fetch_generator(url, limit, params=params)

    def objects(self, object_id, fields=None, relationship=None):
        """
        Get object details. Allows you to limit the fields returned in the
        object's details. Also allows you to provide a relationship. If a
        relationship is provided, the related objects will be returned instead
        of the object itself.

        :param object_id: The object-id of the object to get details for.
        :type object_id: str
        :param fields: The fields to limit the details to.
        :type fields: None, str, list
        :param relationship: The relationship to find other related objects with.
        :type relationship: None, str
        :returns: dict (using json.loads()) for a single object, Generator if
                  using relationships
        """

        if object_id is None or len(object_id) < 1:
            raise pytxValueError("Must provide an object_id")
        url = self._URL + object_id + '/'
        if relationship:
            url = url + relationship + '/'
        params = self._build_get_parameters()
        if isinstance(fields, basestring):
            fields = fields.split(',')
        if fields is not None and not isinstance(fields, list):
            raise pytxValueError("fields must be a list")
        if fields is not None:
            params['fields'] = ','.join(f.strip() for f in fields)
        if relationship:
            return self._fetch_generator(url, -1, params=params)
        else:
            return self.get_object(url, params=params)

    # POST REQUESTS

    def create_threat_indicator(self, params):
        # create a new Threat Indicator using the params dictionary
        return

    def edit(self, object_id, params):
        # edit this object using the params dictionary
        return

    def expire(self, object_id, timestamp):
        # set this object's expired_on to the timestamp to expire it
        return

    def false_positive(self, object_id):
        # use vocabulary.Status to set this object's status to NON_MALICIOUS
        return

    def add_relationship(self, object_id_1, object_id_2):
        # use HTTP POST and create a relationship between two objects
        # /<object_id_1>/related?related_id=<object_id_2>
        return

    # DELETE REQUESTS

    def delete_relationship(self, object_id_1, object_id_2):
        # use HTTP DELETE and remove the relationship between two objects
        # /<object_id_1>/related?related_id=<object_id_2>
        return
