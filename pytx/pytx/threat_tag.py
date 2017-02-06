from .common import Common
from .vocabulary import ThreatTag as tt
from .vocabulary import ThreatExchange as t


class ThreatTag(Common):

    _URL = t.URL + t.VERSION + t.THREAT_TAGS
    _DETAILS = t.URL + t.VERSION
    _RELATED = t.URL + t.VERSION

    _fields = [
        tt.ID,
        tt.NAME,
        tt.TAGGED_OBJECTS,
        tt.TEXT,
        tt.TYPE,
    ]

    _default_fields = [
        tt.ID,
        tt.NAME,
        tt.TAGGED_OBJECTS,
        tt.TEXT,
        tt.TYPE,
    ]

    _unique = [
    ]
