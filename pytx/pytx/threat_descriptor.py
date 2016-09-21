from .common import Common
from .vocabulary import ThreatDescriptor as td
from .vocabulary import ThreatExchange as t


class ThreatDescriptor(Common):

    _URL = t.URL + t.VERSION + t.THREAT_DESCRIPTORS
    _DETAILS = t.URL + t.VERSION
    _RELATED = t.URL + t.VERSION

    _fields = [
        td.ADDED_ON,
        td.ATTACK_TYPE,
        td.CONFIDENCE,
        td.DESCRIPTION,
        td.EXPIRED_ON,
        td.ID,
        td.INDICATOR,
        td.LAST_UPDATED,
        td.METADATA,
        td.MY_REACTIONS,
        td.OWNER,
        td.PRECISION,
        td.PRIVACY_MEMBERS,
        td.PRIVACY_TYPE,
        td.RAW_INDICATOR,
        td.REVIEW_STATUS,
        td.SEVERITY,
        td.SHARE_LEVEL,
        td.SOURCE_URI,
        td.STATUS,
        td.TAGS,
        td.THREAT_TYPE,
        td.TYPE,
    ]

    _default_fields = [
        td.ADDED_ON,
        td.ATTACK_TYPE,
        td.CONFIDENCE,
        td.DESCRIPTION,
        td.EXPIRED_ON,
        td.ID,
        td.INDICATOR,
        td.LAST_UPDATED,
        td.METADATA,
        td.MY_REACTIONS,
        td.OWNER,
        td.PRECISION,
        td.PRIVACY_MEMBERS,
        td.PRIVACY_TYPE,
        td.RAW_INDICATOR,
        td.REVIEW_STATUS,
        td.SEVERITY,
        td.SHARE_LEVEL,
        td.SOURCE_URI,
        td.STATUS,
        td.TAGS,
        td.THREAT_TYPE,
        td.TYPE,
    ]

    _connections = [
    ]

    _unique = [
    ]
