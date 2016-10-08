from .common import Common
from .vocabulary import ThreatIndicator as ti
from .vocabulary import ThreatExchange as t
from .vocabulary import Connection as c


class ThreatIndicator(Common):

    _URL = t.URL + t.VERSION + t.THREAT_INDICATORS
    _DETAILS = t.URL + t.VERSION
    _RELATED = t.URL + t.VERSION

    _fields = [
        ti.ID,
        ti.INDICATOR,
        ti.METADATA,
        ti.TYPE,
    ]

    _default_fields = [
        ti.ID,
        ti.INDICATOR,
        ti.METADATA,
        ti.TYPE,
    ]

    _connections = [
        c.DESCRIPTORS,
        c.MALWARE_ANALYSES,
        c.RELATED,
    ]

    _unique = [
    ]
