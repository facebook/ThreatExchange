from common import Common
from vocabulary import ThreatIndicator as ti
from vocabulary import ThreatExchange as t


class ThreatIndicator(Common):

    _URL = t.URL + t.VERSION + t.THREAT_INDICATORS
    _DETAILS = t.URL
    _RELATED = t.URL

    _fields = [
        ti.ADDED_ON,
        ti.CONFIDENCE,
        ti.DESCRIPTION,
        ti.EXPIRED_ON,
        ti.ID,
        ti.INDICATOR,
        ti.METADATA,
        ti.PASSWORDS,
        ti.PRIVACY_TYPE,
        ti.PRIVACY_MEMBERS,
        ti.REPORT_URLS,
        ti.SEVERITY,
        ti.SHARE_LEVEL,
        ti.STATUS,
        ti.SUBMITTER_COUNT,
        ti.THREAT_TYPE,
        ti.THREAT_TYPES,
        ti.TYPE
    ]

    _unique = [
    ]
