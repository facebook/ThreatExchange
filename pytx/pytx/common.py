from sys import version_info

from .request import Broker

from .vocabulary import Common as c
from .vocabulary import Status as s
from .vocabulary import ThreatExchange as t
from .vocabulary import ThreatDescriptor as td
from .vocabulary import PrivacyType as pt
from .vocabulary import Connection as conn
from .errors import (
    pytxAttributeError,
    pytxValueError
)


#  Python 3 comparability hack
if version_info[0] >= 3:
    basestring = str


class class_or_instance_method(object):

    """
    Custom decorator. This binds to the class if no instance is available,
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
        if name == c.ID:
            self._DETAILS = t.URL + t.VERSION + value + '/'
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
    def objects(cls,
                text=None,
                strict_text=False,
                type_=None,
                sample_type=None,
                fields=None,
                limit=None,
                since=None,
                until=None,
                include_expired=False,
                max_confidence=None,
                min_confidence=None,
                owner=None,
                status=None,
                review_status=None,
                share_level=None,
                sort_by=None,
                sort_order=None,
                __raw__=None,
                full_response=False,
                dict_generator=False,
                request_dict=False,
                retries=None,
                headers=None,
                proxies=None,
                verify=None):
        """
        Get objects from ThreatExchange.

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
        :type include_expired: bool
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
        :param sort_order: The sort order for results. Ascending or descending.
        :type sort_order: str
        :param __raw__: Provide a dictionary to force as GET parameters.
                        Overrides all other arguments.
        :type __raw__: dict
        :param full_response: Return the full response instead of the generator.
                              Takes precedence over dict_generator.
        :type full_response: bool
        :param dict_generator: Return a dictionary instead of an instantiated
                               object.
        :type dict_generator: bool
        :param request_dict: Return a request dictionary only.
        :type request_dict: bool
        :param retries: Number of retries to fetch a page before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: Generator, dict (using json.loads()), str
        """

        if fields is None:
            fields = cls._default_fields
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
                sample_type=sample_type,
                fields=fields,
                limit=limit,
                since=since,
                until=until,
                include_expired=include_expired,
                max_confidence=max_confidence,
                min_confidence=min_confidence,
                owner=owner,
                status=status,
                review_status=review_status,
                share_level=share_level,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        if request_dict:
            return Broker.request_dict('GET',
                                       cls._URL,
                                       params=params)
        if full_response:
            return Broker.get(cls._URL,
                              params=params,
                              retries=retries,
                              headers=headers,
                              proxies=proxies,
                              verify=verify)
        else:
            return Broker.get_generator(cls,
                                        cls._URL,
                                        to_dict=dict_generator,
                                        params=params,
                                        retries=retries,
                                        headers=headers,
                                        proxies=proxies,
                                        verify=verify)

    @class_or_instance_method
    def details(cls_or_self,
                id=None,
                fields=None,
                full_response=False,
                dict_generator=False,
                request_dict=False,
                retries=None,
                headers=None,
                proxies=None,
                verify=None,
                metadata=False):
        """
        Get object details. Allows you to limit the fields returned in the
        object's details.

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
        :param full_response: Return the full response instead of the generator.
                              Takes precedence over dict_generator.
        :type full_response: bool
        :param dict_generator: Return a dictionary instead of an instantiated
                               object.
        :type dict_generator: bool
        :param retries: Number of retries to fetch a page before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :param metadata: Get extra metadata in the response.
        :type metadata: bool
        :returns: Generator, dict, class
        """

        if isinstance(cls_or_self, type):
            url = t.URL + t.VERSION + id + '/'
        else:
            url = cls_or_self._DETAILS
        params = Broker.build_get_parameters()
        if fields is None:
            fields = cls_or_self._fields
        if isinstance(fields, basestring):
            fields = fields.split(',')
        if fields is not None and not isinstance(fields, list):
            raise pytxValueError('fields must be a list')
        if fields is not None:
            params[t.FIELDS] = ','.join(f.strip() for f in fields)
        if metadata:
            params[t.METADATA] = 1
        if full_response:
            return Broker.get(url,
                              params=params,
                              retries=retries,
                              headers=headers,
                              proxies=proxies,
                              verify=verify)
        else:
            if isinstance(cls_or_self, type):
                return Broker.get_new(cls_or_self,
                                      Broker.get(url,
                                                 params=params,
                                                 retries=retries,
                                                 headers=headers,
                                                 proxies=proxies,
                                                 verify=verify))
            else:
                cls_or_self.populate(Broker.get(url,
                                                params=params,
                                                retries=retries,
                                                headers=headers,
                                                proxies=proxies,
                                                verify=verify))
                cls_or_self._changed = []

    @class_or_instance_method
    def connections(cls_or_self,
                    id=None,
                    connection=None,
                    fields=None,
                    limit=None,
                    full_response=False,
                    dict_generator=False,
                    request_dict=False,
                    retries=None,
                    headers=None,
                    proxies=None,
                    verify=None,
                    metadata=False):
        """
        Get object connections. Allows you to limit the fields returned for the
        objects.

        NOTE: This method can be used on both instantiated and uninstantiated
        classes like so:

            foo = ThreatIndicator(id='1234')
            foo.connections(connection='foo')

            foo = ThreatIndicator.connections(id='1234'
                                             connection='foo')

        :param id: The ID of the object to get connections for if the class is
                   not instantiated.
        :type id: str
        :param fields: The fields to limit the details to.
        :type fields: None, str, list
        :param limit: Limit the results.
        :type limit: None, int
        :param connection: The connection to find other related objects with.
        :type connection: None, str
        :param full_response: Return the full response instead of the generator.
                              Takes precedence over dict_generator.
        :type full_response: bool
        :param dict_generator: Return a dictionary instead of an instantiated
                               object.
        :type dict_generator: bool
        :param request_dict: Return a request dictionary only.
        :type request_dict: bool
        :param retries: Number of retries to fetch a page before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :param metadata: Get extra metadata in the response.
        :type metadata: bool
        :returns: Generator, dict, class, str
        """

        if isinstance(cls_or_self, type):
            url = t.URL + t.VERSION + id + '/'
        else:
            url = cls_or_self._DETAILS
        if connection:
            url = url + connection + '/'
        params = Broker.build_get_parameters(limit=limit)
        if isinstance(fields, basestring):
            fields = fields.split(',')
        if fields is not None and not isinstance(fields, list):
            raise pytxValueError('fields must be a list')
        if fields is not None:
            params[t.FIELDS] = ','.join(f.strip() for f in fields)
        if metadata:
            params[t.METADATA] = 1
        if request_dict:
            return Broker.request_dict('GET',
                                       url,
                                       params=params)
        if full_response:
            return Broker.get(url,
                              params=params,
                              retries=retries,
                              headers=headers,
                              proxies=proxies,
                              verify=verify)
        else:
            # Avoid circular imports
            from .malware import Malware
            from .malware_family import MalwareFamily
            from .threat_indicator import ThreatIndicator
            from .threat_descriptor import ThreatDescriptor
            from .threat_exchange_member import ThreatExchangeMember
            from .threat_tag import ThreatTag
            conns = {
                conn.DESCRIPTORS: ThreatDescriptor,
                conn.DROPPED: Malware,
                conn.DROPPED_BY: Malware,
                conn.FAMILIES: MalwareFamily,
                conn.MALWARE_ANALYSES: Malware,
                conn.MEMBERS: ThreatExchangeMember,
                conn.RELATED: ThreatIndicator,
                conn.SIMILAR_MALWARE: Malware,
                conn.TAGGED_OBJECTS: ThreatTag,
                conn.THREAT_INDICATORS: ThreatIndicator,
                conn.VARIANTS: Malware,
            }
            klass = conns.get(connection, None)
            return Broker.get_generator(klass,
                                        url,
                                        to_dict=dict_generator,
                                        params=params,
                                        retries=retries,
                                        headers=headers,
                                        proxies=proxies,
                                        verify=verify)

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
    def new(cls,
            params,
            request_dict=False,
            retries=None,
            headers=None,
            proxies=None,
            verify=None):
        """
        Submit params to the graph to add an object. We will submit to the
        object URL used for creating new objects in the graph. When submitting
        new objects you must provide privacy type and privacy members if the
        privacy type is something other than visible.

        :param params: The parameters to submit.
        :type params: dict
        :param request_dict: Return a request dictionary only.
        :type request_dict: bool
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: dict (using json.loads()), str
        """

        if cls.__name__ != 'ThreatPrivacyGroup':
            if td.PRIVACY_TYPE not in params:
                raise pytxValueError('Must provide a %s' % td.PRIVACY_TYPE)
                pass
            else:
                if (params[td.PRIVACY_TYPE] != pt.VISIBLE and
                        len(params[td.PRIVACY_MEMBERS].split(',')) < 1):
                    raise pytxValueError('Must provide %s' % td.PRIVACY_MEMBERS)
        if request_dict:
            return Broker.request_dict('POST',
                                       cls._URL,
                                       body=params)
        return Broker.post(cls._URL,
                           params=params,
                           retries=retries,
                           headers=headers,
                           proxies=proxies,
                           verify=verify)

    def save(self,
             params=None,
             request_dict=False,
             retries=None,
             headers=None,
             proxies=None,
             verify=None):
        """
        Submit changes to the graph to update an object. We will determine the
        Details URL and submit there (used for updating an existing object). If
        no parameters are provided, we will try to use get_changed() which may
        or may not be accurate (you have been warned!).

        :param params: The parameters to submit.
        :type params: dict
        :param request_dict: Return a request dictionary only.
        :type request_dict: bool
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: dict (using json.loads()), str
        """

        if params is None:
            params = self.get_changed()
        if request_dict:
            return Broker.request_dict('POST',
                                       self._DETAILS,
                                       body=params)
        return Broker.post(self._DETAILS,
                           params=params,
                           retries=retries,
                           headers=headers,
                           proxies=proxies,
                           verify=verify)

    @class_or_instance_method
    def send(cls_or_self,
             id_=None,
             params=None,
             type_=None,
             request_dict=False,
             retries=None,
             headers=None,
             proxies=None,
             verify=None):
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
        :param request_dict: Return a request dictionary only.
        :type request_dict: bool
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: dict (using json.loads()), str
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
            if request_dict:
                return Broker.request_dict('GET',
                                           url,
                                           params=params)
            return Broker.get(url,
                              params=params,
                              retries=retries,
                              headers=headers,
                              proxies=proxies,
                              verify=verify)
        else:
            if request_dict:
                return Broker.request_dict('POST',
                                           url,
                                           body=params)
            return Broker.post(url,
                               params=params,
                               retries=retries,
                               headers=headers,
                               proxies=proxies,
                               verify=verify)

    def expire(self,
               timestamp,
               retries=None,
               headers=None,
               proxies=None,
               verify=None):
        """
        Expire by setting the 'expired_on' timestamp.

        :param timestamp: The timestamp to set for an expiration date.
        :type timestamp: str
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: dict (using json.loads())
        """

        Broker.is_timestamp(timestamp)
        params = {
            td.EXPIRED_ON: timestamp
        }
        return Broker.post(self._DETAILS,
                           params=params,
                           retries=retries,
                           headers=headers,
                           proxies=proxies,
                           verify=verify)

    def false_positive(self,
                       object_id,
                       retries=None,
                       headers=None,
                       proxies=None,
                       verify=None):
        """
        Mark an object as a false positive by setting the status to
        UNKNOWN.

        :param object_id: The object-id of the object to mark.
        :type object_id: str
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: dict (using json.loads())
        """

        params = {
            c.STATUS: s.UNKNOWN
        }
        return Broker.post(self._DETAILS,
                           params=params,
                           retries=retries,
                           headers=headers,
                           proxies=proxies,
                           verify=verify)

    def add_connection(self,
                       object_id,
                       retries=None,
                       headers=None,
                       proxies=None,
                       verify=None):
        """
        Use HTTP POST and add a connection between two objects.

        :param object_id: The other object-id in the connection.
        :type object_id: str
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: dict (using json.loads())
        """

        params = {
            t.RELATED_ID: object_id
        }
        return Broker.post(self._RELATED,
                           params=params,
                           retries=retries,
                           headers=headers,
                           proxies=proxies,
                           verify=verify)

    # DELETE REQUESTS

    def delete_connection(self,
                          object_id,
                          retries=None,
                          headers=None,
                          proxies=None,
                          verify=None):
        """
        Use HTTP DELETE and remove the connection to another object.

        :param object_id: The other object-id in the connection.
        :type object_id: str
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: dict (using json.loads())
        """

        params = {
            t.RELATED_ID: object_id
        }
        return Broker.delete(self._RELATED,
                             params=params,
                             retries=retries,
                             headers=headers,
                             proxies=proxies,
                             verify=verify)

    def react(self,
              reaction,
              retries=None,
              headers=None,
              proxies=None,
              verify=None):
        """
        React to this object.

        :param reaction: The reaction to provide.
        :type reaction: str
        :param retries: Number of retries to submit before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: dict (using json.loads())
        """

        params = {
            t.REACTIONS: reaction
        }
        return Broker.post(self._DETAILS,
                           params=params,
                           retries=retries,
                           headers=headers,
                           proxies=proxies,
                           verify=verify)
