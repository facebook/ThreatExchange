from .access_token import get_app_id
from .common import Common
from .request import Broker
from .vocabulary import ThreatPrivacyGroup as tpg
from .vocabulary import ThreatExchange as t
from .vocabulary import Connection as c
from .errors import pytxValueError


class ThreatPrivacyGroup(Common):

    _URL = t.URL + t.VERSION + t.THREAT_PRIVACY_GROUPS
    _DETAILS = t.URL + t.VERSION
    _RELATED = t.URL + t.VERSION

    _fields = [
        tpg.ID,
        tpg.NAME,
        tpg.DESCRIPTION,
        tpg.MEMBERS_CAN_SEE,
        tpg.MEMBERS_CAN_USE,
    ]

    _default_fields = [
        tpg.ID,
        tpg.NAME,
        tpg.DESCRIPTION,
        tpg.MEMBERS_CAN_SEE,
        tpg.MEMBERS_CAN_USE,
    ]

    _connections = [
        c.MEMBERS,
    ]

    _unique = [
    ]

    @classmethod
    def mine(cls,
             role=None,
             full_response=False,
             dict_generator=False,
             retries=None,
             headers=None,
             proxies=None,
             verify=None):
        """
        Find all of the Threat Privacy Groups that I am either the owner or a
        member.

        :param role: Whether you are an 'owner' or a 'member'
        :type role: str
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
        :returns: Generator, dict (using json.loads())
        """

        if role is None:
            raise pytxValueError('Must provide a role')
        app_id = get_app_id() + '/'
        if role == 'owner':
            role = t.THREAT_PRIVACY_GROUPS_OWNER
        elif role == 'member':
            role = t.THREAT_PRIVACY_GROUPS_MEMBER
        else:
            raise pytxValueError('Role must be "owner" or "member"')
        params = {'fields': ','.join(cls._fields)}
        url = t.URL + t.VERSION + app_id + role
        if full_response:
            return Broker.get(url,
                              params=params,
                              retries=retries,
                              headers=headers,
                              proxies=proxies,
                              verify=verify)
        else:
            return Broker.get_generator(cls,
                                        url,
                                        params=params,
                                        to_dict=dict_generator,
                                        retries=retries,
                                        headers=headers,
                                        proxies=proxies,
                                        verify=verify)

    def get_members(self,
                    retries=None,
                    headers=None,
                    proxies=None,
                    verify=None):
        """
        Get the members of a Threat Privacy Group

        :param retries: Number of retries to fetch a page before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: list
        """

        url = self._DETAILS + tpg.MEMBERS
        results = Broker.get(url,
                             retries=retries,
                             headers=headers,
                             proxies=proxies,
                             verify=verify)
        if t.DATA in results:
            return results[t.DATA]
        else:
            return []

    def set_members(self,
                    members=None,
                    retries=None,
                    headers=None,
                    proxies=None,
                    verify=None):
        """
        Set the members of a Threat Privacy Group

        :param members: str or list of member IDs to add as members.
        :type members: str or list
        :param retries: Number of retries to fetch a page before stopping.
        :type retries: int
        :param headers: header info for requests.
        :type headers: dict
        :param proxies: proxy info for requests.
        :type proxies: dict
        :param verify: verify info for requests.
        :type verify: bool, str
        :returns: list
        """

        if members is None:
            raise pytxValueError('Must provide members as a str or list')
        elif isinstance(members, list):
            members = ','.join(members)
        return Broker.post(self._DETAILS,
                           params={'members': members},
                           retries=retries,
                           headers=headers,
                           proxies=proxies,
                           verify=verify)
