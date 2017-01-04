import json
import requests
import urllib

from requests.packages.urllib3.util import Retry

from .access_token import get_access_token
from .connection import get_headers, get_proxies, get_verify
from .logger import do_log, log_message

from .vocabulary import ThreatExchange as t
from .vocabulary import Paging as p
from .vocabulary import PagingCursor as pc
from .vocabulary import Response as R
from .errors import (
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
        n._changed = []
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
        except ValueError as e:
            raise pytxValueError(e)
        return

    @staticmethod
    def sanitize_bool(value):
        """
        If value is provided, sanitize it.

        'true' will be used if value is in [True, 'true', 'True', 1].
        'false' will be used if value is in [False, 'false', 'False', 0].

        If we receive any other value value will be set to None and
        ignored when building the GET request.

        :param value: The value to sanitize.
        :type value: bool, str, int
        :returns: str, None
        """

        if value in (True, 'true', 'True', 1):
            value = 'true'
        elif value in (False, 'false', 'False', 0):
            value = 'false'
        else:
            value = None
        return value

    @staticmethod
    def handle_results(resp):
        """
        Handle the results of a request.

        :param resp: The HTTP response.
        :type resp: response object
        :returns: dict (using json.loads())
        """

        if resp.status_code != 200:
            error = json.loads(resp.text).get(R.ERROR, None)
            response = {}
            response['status_code'] = resp.status_code
            response['url'] = resp.url
            if error:
                response[R.MESSAGE] = error.get(R.MESSAGE, None)
                response[R.TYPE] = error.get(R.TYPE, None)
                response[R.CODE] = error.get(R.CODE, None)
                response[R.FBTRACE_ID] = error.get(R.FBTRACE_ID, None)
            raise pytxFetchError(response)
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
    def build_get_parameters(cls,
                             text=None,
                             strict_text=None,
                             type_=None,
                             sample_type=None,
                             fields=None,
                             limit=None,
                             since=None,
                             until=None,
                             include_expired=None,
                             max_confidence=None,
                             min_confidence=None,
                             owner=None,
                             status=None,
                             review_status=None,
                             share_level=None,
                             sort_by=None,
                             sort_order=None):
        """
        Validate arguments and convert them into GET parameters.

        :param text: The text used for limiting the search.
        :type text: str
        :param strict_text: Whether we should use strict searching.
        :type strict_text: bool, str, int
        :param type_: The Indicator type to limit to.
        :type type_: str
        :param sample_type: The Sample type to limit to.
        :type sample_type: str
        :param fields: Select specific fields to pull
        :type fields: str, list
        :param limit: The maximum number of objects to return.
        :type limit: int, str
        :param since: The timestamp to limit the beginning of the search.
        :type since: str
        :param until: The timestamp to limit the end of the search.
        :type until: str
        :param include_expired: Include expired content in your results.
        :type until: bool, str, int
        :param max_confidence: The max confidence level to search for.
        :type max_confidence: int
        :param min_confidence: The min confidence level to search for.
        :type min_confidence: int
        :param owner: The owner to limit to. This can be comma-delimited to
                      include multiple owners.
        :type owner: str
        :param status: The status to limit to.
        :type status: str
        :param review_status: The review status to limit to.
        :type review_status: str
        :param share_level: The share level to limit to.
        :type share_level: str
        :param sort_by: Sort by relevance or create time.
        :type sort_by: str
        :param sort_order: The sort order for results.
        :type sort_order: str
        :returns: dict
        """

        cls.validate_get(limit, since, until)
        strict = cls.sanitize_bool(strict_text)
        include_expired = cls.sanitize_bool(include_expired)
        params = {}
        if text:
            params[t.TEXT] = text
        if strict is not None:
            params[t.STRICT_TEXT] = strict
        if type_:
            params[t.TYPE] = type_
        if fields:
            params[t.FIELDS] = ','.join(fields) if isinstance(fields, list) else fields
        if limit:
            params[t.LIMIT] = limit
        if since:
            params[t.SINCE] = since
        if until:
            params[t.UNTIL] = until
        if include_expired is not None:
            params[t.INCLUDE_EXPIRED] = include_expired
        if max_confidence:
            params[t.MAX_CONFIDENCE] = max_confidence
        if min_confidence:
            params[t.MIN_CONFIDENCE] = min_confidence
        if owner:
            params[t.OWNER] = owner
        if sample_type:
            params[t.SAMPLE_TYPE] = sample_type
        if status:
            params[t.STATUS] = status
        if review_status:
            params[t.REVIEW_STATUS] = review_status
        if share_level:
            params[t.SHARE_LEVEL] = share_level
        if sort_by in (t.RELEVANCE, t.CREATE_TIME):
            params[t.SORT_BY] = sort_by
        if sort_order in (t.ASCENDING, t.DESCENDING):
            params[t.SORT_ORDER] = sort_order
        return params

    @classmethod
    def build_session(cls, retries=None):
        """
        Build custom requests session with retry capabilities.

        :param retries: Number of retries before stopping.
        :type retries: int
        :returns: requests session object
        """

        if retries is None:
            retries = 0
        session = requests.Session()
        session.mount('https://',
                      requests.adapters.HTTPAdapter(
                          max_retries=Retry(total=retries,
                                            status_forcelist=[500, 503]
                                            )
                      ))
        return session

    @classmethod
    def request_dict(cls,
                     type_,
                     url,
                     params=None,
                     body=None):
        """
        Return a dictionary with the request type, URL, and optionally a body.

        :param type_: The request type.
        :type type_: str
        :param url: The request URL.
        :type url: str
        :param params: The parameters to submit.
        :type params: dict
        :param body: The body to submit.
        :type body: str
        :returns: dict
        """

        request = requests.Request(type_, url, params=params)
        prep = request.prepare()
        full_url = prep.url
        if body:
            body = urllib.urlencode(body)
        return {'type': type_,
                'url': full_url,
                'body': body}

    @classmethod
    def get(cls,
            url,
            params=None,
            retries=None,
            headers=None,
            proxies=None,
            verify=None):
        """
        Send a GET request.

        :param url: The URL to send the GET request to.
        :type url: str
        :param params: The GET parameters to send in the request.
        :type params: dict
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

        if not params:
            params = dict()
        if headers is None:
            headers = get_headers()
        if proxies is None:
            proxies = get_proxies()
        if verify is None:
            verify = get_verify()

        params[t.ACCESS_TOKEN] = get_access_token()
        session = cls.build_session(retries)
        resp = session.get(url,
                           params=params,
                           headers=headers,
                           proxies=proxies,
                           verify=verify)
        return cls.handle_results(resp)

    @classmethod
    def post(cls,
             url,
             params=None,
             retries=None,
             headers=None,
             proxies=None,
             verify=None):
        """
        Send a POST request.

        :param url: The URL to send the POST request to.
        :type url: str
        :param params: The POST parameters to send in the request.
        :type params: dict
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

        if not params:
            params = dict()
        if headers is None:
            headers = get_headers()
        if proxies is None:
            proxies = get_proxies()
        if verify is None:
            verify = get_verify()

        params[t.ACCESS_TOKEN] = get_access_token()
        session = cls.build_session(retries)
        resp = session.post(url,
                            params=params,
                            headers=headers,
                            proxies=proxies,
                            verify=verify)
        return cls.handle_results(resp)

    @classmethod
    def delete(cls,
               url,
               params=None,
               retries=None,
               headers=None,
               proxies=None,
               verify=None):
        """
        Send a DELETE request.

        :param url: The URL to send the DELETE request to.
        :type url: str
        :param params: The DELETE parameters to send in the request.
        :type params: dict
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

        if not params:
            params = dict()
        if headers is None:
            headers = get_headers()
        if proxies is None:
            proxies = get_proxies()
        if verify is None:
            verify = get_verify()

        params[t.ACCESS_TOKEN] = get_access_token()
        session = cls.build_session(retries)
        resp = session.delete(url,
                              params=params,
                              headers=headers,
                              proxies=proxies,
                              verify=verify)
        return cls.handle_results(resp)

    @classmethod
    def get_generator(cls,
                      klass,
                      url,
                      to_dict=False,
                      params=None,
                      retries=None,
                      headers=None,
                      proxies=None,
                      verify=None):
        """
        Generator for managing GET requests. For each GET request it will yield
        the next object in the results until there are no more objects. If the
        GET response contains a 'next' value in the 'paging' section, the
        generator will automatically fetch the next set of results and continue
        the process until the total limit has been reached or there is no longer
        a 'next' value.

        :param klass: The class to use for the generator.
        :type klass: class
        :param url: The URL to send the GET request to.
        :type url: str
        :param to_dict: Return a dictionary instead of an instantiated class.
        :type to_dict: bool
        :param params: The GET parameters to send in the request.
        :type params: dict
        :param retries: Number of retries before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: Generator
        """

        if not klass:
            raise pytxValueError('Must provide a valid object to query.')
        if not params:
            params = dict()
        if headers is None:
            headers = get_headers()
        if proxies is None:
            proxies = get_proxies()
        if verify is None:
            verify = get_verify()
        next_ = True
        while next_:
            results = cls.get(url,
                              params=params,
                              retries=retries,
                              headers=headers,
                              proxies=proxies,
                              verify=verify)
            if do_log():
                try:
                    has_paging = results.get(t.PAGING, None)
                    before = ''
                    after = ''
                    if has_paging is not None:
                        before = results[t.PAGING][p.CURSORS].get(pc.BEFORE,
                                                                  'None'
                                                                  )
                        after = results[t.PAGING][p.CURSORS].get(pc.AFTER,
                                                                 'None'
                                                                 )
                    count = len(results[t.DATA])
                    log_message(
                        'Cursor: BEFORE: %s, AFTER: %s, LEN: %d' % (before,
                                                                    after,
                                                                    count
                                                                    )
                    )
                except Exception as e:
                    log_message('Missing key in response: %s' % e)
            for data in results[t.DATA]:
                if to_dict:
                    yield data
                else:
                    yield cls.get_new(klass, data)
            try:
                next_ = results[t.PAGING][t.NEXT]
            except:
                log_message('No next in Pager to follow.')
                next_ = False
            if next_:
                url = next_
                params = {}
