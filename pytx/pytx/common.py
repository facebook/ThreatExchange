from request import Broker

from vocabulary import Common as c
from vocabulary import Status as s
from vocabulary import ThreatExchange as t
from vocabulary import ThreatDescriptor as td
from vocabulary import PrivacyType as pt
from vocabulary import Connection as conn
from errors import (
    pytxAttributeError,
    pytxValueError
)


class class_or_instance_method(object):

    """
    Custom decorator. This binds to the class if no instance is avaialble,
    otherwise it will bind to the instance.

    This allows us to use a single method which can take both "self" and "cls"
    as the first argument.
    """

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        if instance is None:
            return classmethod(self.func).__get__(None, cls)
        return self.func.__get__(instance, cls)


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

    def __init__(self, **kwargs):
        """
        Initialize the object. Set any attributes that were provided.
        """

        for name, value in kwargs.items():
            self.__setattr__(name, value)

    def __setattr__(self, name, value):
        """
        Override __setattr__. If it is the ID being set then we will set the
        URLs to leverage the ID (used when instantiating classes with data
        returned from a GET request).

        If the attribute was changed from a previous value, we will add it to
        _changed in the event this is an edit.

        :param name: The name of the attribute to set.
        :type name: str
        :param value: The value to set the attribute to.
        :type value: None, int, str, bool
        """

        object.__setattr__(self, name, value)
        if name == c.ID and value not in self._DETAILS:
            self._DETAILS = self._DETAILS + value + '/'
            self._RELATED = self._DETAILS + t.RELATED
        if name not in self._changed and name in self._fields:
            self._changed.append(name)

    def __getattr__(self, attr):
        """
        Get an attribute. If the attribute does not exist, return None
        """

        if attr not in self._fields + self._internal + self._unique:
            raise pytxAttributeError('%s is not a valid attribute' % attr)

        try:
            return object.__getattribute__(self, attr)
        except:
            return None

    def set(self, name, value):
        """
        Wrapper around __setattr__ making it easier to use the vocabulary to set
        class attributes.

        :param name: The name of the attribute to set.
        :type name: str
        :param value: The value to set the attribute to.
        :type value: None, int, str, bool
        """

        return self.__setattr__(name, value)

    def get(self, attr):
        """
        Wrapper around __getattr__ making it easier to use the vocabulary to get
        class attributes.

        :param attr: The name of the attribute to get.
        :type attr: str
        """

        return self.__getattr__(attr)

    def populate(self, attrs):
        """
        Given a dictionary, populate self with the keys as attributes.

        :param attrs: A dictionary used as attributes and values.
        :type attrs: dict
        """

        for k, v in attrs.iteritems():
            self.set(k, v)

    def to_dict(self):
        """
        Convert this object into a dictionary.

        :returns: dict
        """

        d = dict(
            (n, getattr(self, n, None)) for n in self._fields
        )
        return d

    @classmethod
    def objects(cls, text=None, strict_text=False, type_=None, threat_type=None,
                fields=None, limit=None, since=None, until=None, __raw__=None,
                full_response=False, dict_generator=False, retries=None):
        """
        Get objects from ThreatExchange.

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
        :param __raw__: Provide a dictionary to force as GET parameters.
                        Overrides all other arguments.
        :type __raw__: dict
        :param full_response: Return the full response instead of the generator.
                              Takes precedence over dict_generator.
        :type full_response: bool
        :param dict_generator: Return a dictionary instead of an instantiated
                               object.
        :type dict_generator: bool
        :param retries: Number of retries to fetch a page before stopping.
        :type retries: int
        :returns: Generator, dict (using json.loads())
        """

        if __raw__:
            if isinstance(__raw__, dict):
                params = __raw__
            else:
                raise pytxValueError('__raw__ must be of type dict')
        else:
            params = Broker.build_get_parameters(
                text=text,
                strict_text=strict_text,
                type_=type_,
                threat_type=threat_type,
                fields=fields,
                limit=limit,
                since=since,
                until=until,
            )
        if full_response:
            return Broker.get(cls._URL, params=params, retries=retries)
        else:
            return Broker.get_generator(cls,
                                        cls._URL,
                                        to_dict=dict_generator,
                                        params=params,
                                        retries=retries)

    @class_or_instance_method
    def details(cls_or_self, id=None, fields=None, connection=None,
                full_response=False, dict_generator=False, retries=None,
                metadata=False):
        """
        Get object details. Allows you to limit the fields returned in the
        object's details. Also allows you to provide a connection. If a
        connection is provided, the related objects will be returned instead
        of the object itself.

        NOTE: This method can be used on both instantiated and uninstantiated
        classes like so:

            foo = ThreatIndicator(id='1234')
            foo.details()

            foo = ThreatIndicator.details(id='1234')


        BE AWARE: Due to the nature of ThreatExchange allowing you to query for
        an object by ID but not actually telling you the type of object returned
        to you, using an ID for an object of a different type (ex: ID for a
        Malware object using ThreatIndicator class) will result in the wrong
        object populated with only data that is common between the two objects.

        :param id: The ID of the object to get details for if the class is not
                   instantiated.
        :type id: str
        :param fields: The fields to limit the details to.
        :type fields: None, str, list
        :param connection: The connection to find other related objects with.
        :type connection: None, str
        :param full_response: Return the full response instead of the generator.
                              Takes precedence over dict_generator.
        :type full_response: bool
        :param dict_generator: Return a dictionary instead of an instantiated
                               object.
        :type dict_generator: bool
        :param retries: Number of retries to fetch a page before stopping.
        :type retries: int
        :param metadata: Get extra metadata in the response.
        :type metadata: bool
        :returns: Generator, dict, class
        """

        if isinstance(cls_or_self, type):
            url = t.URL + t.VERSION + id + '/'
        else:
            url = cls_or_self._DETAILS
        if connection:
            url = url + connection + '/'
        params = Broker.build_get_parameters()
        if isinstance(fields, basestring):
            fields = fields.split(',')
        if fields is not None and not isinstance(fields, list):
            raise pytxValueError('fields must be a list')
        if fields is not None:
            params[t.FIELDS] = ','.join(f.strip() for f in fields)
        if metadata:
            params[t.METADATA] = 1
        if full_response:
            return Broker.get(url, params=params, retries=retries)
        else:
            if connection:
                # Avoid circular imports
                from malware import Malware
                from malware_family import MalwareFamily
                from threat_indicator import ThreatIndicator
                from threat_descriptor import ThreatDescriptor
                conns = {
                    conn.DESCRIPTORS: ThreatDescriptor,
                    conn.DROPPED: Malware,
                    conn.DROPPED_BY: Malware,
                    conn.FAMILIES: MalwareFamily,
                    conn.MALWARE_ANALYSES: Malware,
                    conn.RELATED: ThreatIndicator,
                    conn.THREAT_INDICATORS: ThreatIndicator,
                    conn.VARIANTS: Malware,
                }
                klass = conns.get(connection, None)
                return Broker.get_generator(klass,
                                            url,
                                            to_dict=dict_generator,
                                            params=params,
                                            retries=retries)
            else:
                if isinstance(cls_or_self, type):
                    return Broker.get_new(cls_or_self,
                                          Broker.get(url,
                                                     params=params,
                                                     retries=retries))
                else:
                    cls_or_self.populate(Broker.get(url,
                                                    params=params,
                                                    retries=retries))
                    cls_or_self._changed = []

    def get_changed(self):
        """
        Generate a dict of all of the changed attributes for this class. Useful
        for generating parameters to submit for saving.

        :returns: dict
        """

        return dict(
            (n, getattr(self, n)) for n in self._changed if n != c.ID
        )

    @classmethod
    def new(cls, params, retries=None):
        """
        Submit params to the graph to add an object. We will submit to the
        object URL used for creating new objects in the graph. When submitting
        new objects you must provide privacy type and privacy members if the
        privacy type is something other than visible.

        :param params: The parameters to submit.
        :type params: dict
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :returns: dict (using json.loads())
        """

        if td.PRIVACY_TYPE not in params:
            raise pytxValueError('Must provide a %s' % td.PRIVACY_TYPE)
            pass
        else:
            if (params[td.PRIVACY_TYPE] != pt.VISIBLE and
                    len(params[td.PRIVACY_MEMBERS].split(',')) < 1):
                raise pytxValueError('Must provide %s' % td.PRIVACY_MEMBERS)
        return Broker.post(cls._URL, params=params, retries=retries)

    def save(self, params=None, retries=None):
        """
        Submit changes to the graph to update an object. We will determine the
        Details URL and submit there (used for updating an existing object). If
        no parameters are provided, we will try to use get_changed() which may
        or may not be accurate (you have been warned!).

        :param params: The parameters to submit.
        :type params: dict
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :returns: dict (using json.loads())
        """

        if params is None:
            params = self.get_changed()
        return Broker.post(self._DETAILS, params=params, retries=retries)

    @class_or_instance_method
    def send(cls_or_self, id_=None, params=None, type_=None, retries=None):
        """
        Send custom params to the object URL. If `id` is provided it will be
        appended to the URL. If this is an uninstantiated class we will use the
        object type url (ex: /threat_descriptors/). If this is an instantiated
        object we will use the details URL. The type_ should be either GET or
        POST. We will default to GET if this is an uninstantiated class, and
        POST if this is an instantiated class.

        :param id_: ID of a graph object.
        :type id_: str
        :param params: Parameters to submit in the request.
        :type params: dict
        :param type_: GET or POST
        :type type_: str
        :param retries: Number of retries to submit before stopping.
        :type retries: int

        :returns: dict (using json.loads())
        """

        if isinstance(cls_or_self, type):
            url = cls_or_self._URL
            if type_ is None:
                type_ = 'GET'
        else:
            url = cls_or_self._DETAILS
            if type_ is None:
                type_ = 'POST'
        if id_ is not None and len(id_) > 0:
            url = url + id_ + '/'
        if params is None:
            params = {}
        if type_ == 'GET':
            return Broker.get(url, params=params, retries=retries)
        else:
            return Broker.post(url, params=params, retries=retries)

    def expire(self, timestamp, retries=None):
        """
        Expire by setting the 'expired_on' timestamp.

        :param timestamp: The timestamp to set for an expiration date.
        :type timestamp: str
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :returns: dict (using json.loads())
        """

        Broker.is_timestamp(timestamp)
        params = {
            td.EXPIRED_ON: timestamp
        }
        return Broker.post(self._DETAILS, params=params, retries=retries)

    def false_positive(self, object_id, retries=None):
        """
        Mark an object as a false positive by setting the status to
        UNKNOWN.

        :param object_id: The object-id of the object to mark.
        :type object_id: str
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :returns: dict (using json.loads())
        """

        params = {
            c.STATUS: s.UNKNOWN
        }
        return Broker.post(self._DETAILS, params=params, retries=retries)

    def add_connection(self, object_id, retries=None):
        """
        Use HTTP POST and add a connection between two objects.

        :param object_id: The other object-id in the connection.
        :type object_id: str
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :returns: dict (using json.loads())
        """

        params = {
            t.RELATED_ID: object_id
        }
        return Broker.post(self._RELATED, params=params, retries=retries)

    # DELETE REQUESTS

    def delete_connection(self, object_id, retries=None):
        """
        Use HTTP DELETE and remove the connection to another object.

        :param object_id: The other object-id in the connection.
        :type object_id: str
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :returns: dict (using json.loads())
        """

        params = {
            t.RELATED_ID: object_id
        }
        return Broker.delete(self._RELATED, params=params, retries=retries)
