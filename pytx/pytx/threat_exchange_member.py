from request import Broker

from vocabulary import ThreatExchange as t
from vocabulary import ThreatExchangeMember as tem
from errors import pytxAttributeError


class ThreatExchangeMember(object):

    _URL = t.URL + t.VERSION + t.THREAT_EXCHANGE_MEMBERS

    _internal = [
        '_access_token',
    ]

    _fields = [
        tem.ID,
        tem.NAME,
        tem.EMAIL
    ]

    _unique = [
    ]

    def __init__(self, **kwargs):
        """
        Initialize the object. Set the _access_token and any attributes that
        were provided.
        """

        for name, value in kwargs.items():
            self.__setattr__(name, value)

    def __getattr__(self, attr):
        """
        Get an attribute. If the attribute does not exist, return None
        """

        if attr not in self._fields and attr not in self._internal:
            raise pytxAttributeError('%s is not a valid attribute' % attr)

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

    @classmethod
    def _get_generator(cls, url, to_dict=False, params=None):
        """
        Send the GET request and return a generator.

        :param url: The URL to send the GET request to.
        :type url: str
        :param to_dict: Return a dictionary instead of an instantiated class.
        :type to_dict: bool
        :param params: The GET parameters to send in the request.
        :type params: dict
        :returns: Generator, dict (using json.loads())
        """

        if not params:
            params = dict()

        members = Broker.get(url, params=params).get(t.DATA, [])
        total = len(members)
        if total == t.MIN_TOTAL:
            yield None
        else:
            for member in members:
                if to_dict:
                    yield member
                else:
                    yield Broker.get_new(cls, member)

    @classmethod
    def objects(cls, full_response=False, dict_generator=False):
        """
        Get a list of Threat Exchange Members

        :param full_response: Return the full response instead of the generator.
                              Takes precedence over dict_generator.
        :type full_response: bool
        :param dict_generator: Return a dictionary instead of an instantiated
                               object.
        :type dict_generator: bool
        :returns: Generator, dict (using json.loads())
        """

        if full_response:
            return Broker.get(cls._URL)
        else:
            return cls._get_generator(cls._URL,
                                      to_dict=dict_generator)

    def to_dict(self):
        """
        Convert this object into a dictionary.

        :returns: dict
        """

        d = dict(
            (n, getattr(self, n, None)) for n in self._fields
        )
        return d
