import json
import requests


class pytxValueError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class pytxFetchError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class pytx(object):
    _URL                        = 'https://graph.facebook.com/'

    # GET
    _MALWARE_ANALYSES           = 'malware_analyses'
    _THREAT_EXCHANGE_MEMBERS    = 'threat_exchange_members'
    _THREAT_INDICATORS          = 'threat_indicators'

    #POST

    def __init__(self, app_id, app_secret):
        self._access_token = app_id + "|" + app_secret

    @property
    def url(self):
        return self._URL

    @property
    def access_token(self):
        return self._access_token

    def is_timestamp(self, timestamp):
        try:
            int(timestamp)
            return True
        except ValueError, e:
            raise pytxValueError(e)

    def validate_limit(self, limit):
        try:
            int(limit)
        except ValueError, e:
            raise pytxValueError(e)
        if limit > 5000:
            raise pytxValueError("limit cannot exceed 5000 (default: 500)")
        return

    def validate_strict(self, strict):
        return

    def validate_get(self, limit, since, until):
        if since:
            self.is_timestamp(since)
        if until:
            self.is_timestamp(until)
        if limit:
            self.validate_limit(limit)

    def get_strict(self, strict_text):
        if strict_text in (True, 'true', 'True', 1):
            strict = 'true'
        elif strict_text in (False, 'false', 'False', 0):
            strict = 'false'
        else:
            strict = None
        return strict

    def build_get_parameters(self, text=None, strict_text=None, type_=None,
                             limit=None, since=None, until=None):
        self.validate_get(limit, since, until)
        strict = self.get_strict(strict_text)
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
        resp = requests.get(url, params=params)
        if resp.status_code != 200:
            raise pytxFetchError("Response code: %s" % resp.status_code)
        try:
            results = json.loads(resp.text)
        except:
            raise pytxFetchError("Unable to convert response to JSON.")
        return results

    def _fetch_generator(self, url, total, params={}):
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

    def malware_analyses(self, text, strict_text=False, limit=None,
                         since=None, until=None):
        url = self._URL + self._MALWARE_ANALYSES
        params = self.build_get_parameters(
            limit,
            text,
            strict_text,
            since,
            until
        )
        return self._fetch_generator(url, limit, params=params)

    def threat_exchange_members(self):
        url = self._URL + self._THREAT_EXCHANGE_MEMBERS
        params = self.build_get_parameters()
        return self._fetch_generator(url, -1, params=params)

    def threat_indicators(self, text, strict_text=False, type_=None,
                          limit=None, since=None, until=None):
        url = self._URL + self._THREAT_INDICATORS
        params = self.build_get_parameters(
            limit,
            text,
            type_,
            strict_text,
            since,
            until
        )
        return self._fetch_generator(url, limit, params=params)
