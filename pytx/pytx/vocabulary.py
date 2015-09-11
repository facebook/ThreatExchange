class ThreatExchange(object):

    """
    General vocabulary for ThreatExchange.
    """

    URL = 'https://graph.facebook.com/'
    VERSION = 'v2.4/'
    ACCESS_TOKEN = 'access_token'
    DEFAULT_LIMIT = 25

    # GET
    MALWARE_ANALYSES = 'malware_analyses/'
    MALWARE_FAMILIES = 'malware_families/'
    THREAT_EXCHANGE_MEMBERS = 'threat_exchange_members/'
    THREAT_DESCRIPTORS = 'threat_descriptors/'
    THREAT_INDICATORS = 'threat_indicators/'

    FIELDS = 'fields'
    LIMIT = 'limit'
    OWNER = 'owner'
    SINCE = 'since'
    STRICT_TEXT = 'strict_text'
    TEXT = 'text'
    THREAT_TYPE = 'threat_type'
    TYPE = 'type'
    UNTIL = 'until'

    DATA = 'data'
    PAGING = 'paging'
    NEXT = 'next'

    METADATA = 'metadata'

    NO_TOTAL = -1
    MIN_TOTAL = 0
    DEC_TOTAL = 1

    # POST
    RELATED = 'related'
    RELATED_ID = 'related_id'

    # Environment Variables for init()
    TX_ACCESS_TOKEN = 'TX_ACCESS_TOKEN'
    TX_APP_ID = 'TX_APP_ID'
    TX_APP_SECRET = 'TX_APP_SECRET'


class Common(object):

    """
    Vocabulary common to multiple objects.
    """

    ADDED_ON = 'added_on'
    ID = 'id'
    METADATA = 'metadata'
    SHARE_LEVEL = 'share_level'
    STATUS = 'status'
    SUBMITTER_COUNT = 'submitter_count'
    VICTIM_COUNT = 'victim_count'


class Connection(object):

    """
    Vocabulary specific to searching for, creating, or removing connections
    between objects.
    """

    ADDED_ON = Common.ADDED_ON
    CRX = 'crx'
    DESCRIPTORS = 'descriptors'
    DROPPED = 'dropped'
    DROPPED_BY = 'dropped_by'
    FAMILIES = 'families'
    ID = Common.ID
    MALWARE_ANALYSES = 'malware_analyses'
    RELATED = 'related'
    STATUS = Common.STATUS
    THREAT_INDICATORS = 'threat_indicators'
    VARIANTS = 'variants'
    VICTIM_COUNT = Common.VICTIM_COUNT


class Malware(object):

    """
    Vocabulary specific to searching for, creating, or modifying a Malware
    object.
    """

    ADDED_ON = Common.ADDED_ON
    CRX = 'crx'
    ID = Common.ID
    IMPHASH = 'imphash'
    MD5 = 'md5'
    METADATA = Common.METADATA
    PASSWORD = 'password'
    PE_RICH_HEADER = 'pe_rich_header'
    SAMPLE = 'sample'
    SHA1 = 'sha1'
    SHA256 = 'sha256'
    SHARE_LEVEL = Common.SHARE_LEVEL
    SSDEEP = 'ssdeep'
    STATUS = Common.STATUS
    SUBMITTER_COUNT = Common.SUBMITTER_COUNT
    VICTIM_COUNT = Common.VICTIM_COUNT
    XPI = 'xpi'


class MalwareFamilies(object):

    """
    Vocabulary specific to searching for Malware Family objects.
    """

    ADDED_ON = Common.ADDED_ON
    ALIASES = 'aliases'
    DESCRIPTION = 'description'
    FAMILY_TYPE = 'family_type'
    ID = Common.ID
    MALICIOUS = 'malicious'
    NAME = 'name'
    SAMPLE_COUNT = 'sample_count'
    SHARE_LEVEL = Common.SHARE_LEVEL


class Paging(object):

    """
    Vocabulary for the fields available in a GET response specific to paging.
    """

    PAGING = 'paging'
    CURSORS = 'cursors'
    NEXT = 'next'


class PagingCursor(object):

    """
    Vocabulary for describing the paging cursor in a GET response.
    """

    BEFORE = 'before'
    AFTER = 'after'


class Response(object):

    """
    Vocabulary for describing server responses.
    """

    SUCCESS = 'success'
    ID = 'id'


class ThreatExchangeMember(object):

    """
    Vocabulary for describing a ThreatExchangeMember.
    """

    ID = Common.ID
    NAME = 'name'
    EMAIL = 'email'


class ThreatIndicator(object):

    """
    Vocabulary specific to searching for, adding, or modifying a Threat
    Indicator object.
    """

    ID = Common.ID
    INDICATOR = 'indicator'
    METADATA = Common.METADATA
    TYPE = 'type'


class ThreatDescriptor(object):

    """
    Vocabulary specific to searching for, adding, or modifying a Threat
    Indicator object.
    """

    ADDED_ON = 'added_on'
    CONFIDENCE = 'confidence'
    DESCRIPTION = 'description'
    EXPIRED_ON = 'expired_on'
    ID = Common.ID
    INDICATOR = 'indicator'
    LAST_UPDATED = 'last_updated'
    METADATA = Common.METADATA
    OWNER = 'owner'
    PRECISION = 'precision'
    PRIVACY_MEMBERS = 'privacy_members'
    PRIVACY_TYPE = 'privacy_type'
    RAW_INDICATOR = 'raw_indicator'
    REVIEW_STATUS = 'review_status'
    SEVERITY = 'severity'
    SHARE_LEVEL = Common.SHARE_LEVEL
    STATUS = Common.STATUS
    SUBMITTER_COUNT = Common.SUBMITTER_COUNT
    THREAT_TYPE = 'threat_type'     # Used in POST
    THREAT_TYPES = 'threat_types'    # Returned in GET
    TYPE = 'type'


class Attack(object):

    """
    Vocabulary for the Threat Indicator Attack type.
    """

    ACCESS_TOKEN_THEFT = 'ACCESS_TOKEN_THEFT'
    BRUTE_FORCE = 'BRUTE_FORCE'
    CLICKJACKING = 'CLICKJACKING'
    EMAIL_SPAM = 'EMAIL_SPAM'
    FAKE_ACCOUNTS = 'FAKE_ACCOUNTS'
    IP_INFRINGEMENT = 'IP_INFRINGEMENT'
    MALICIOUS_APP = 'MALICIOUS_APP'
    MALWARE = 'MALWARE'
    PHISHING = 'PHISHING'
    SELF_XSS = 'SELF_XSS'
    SHARE_BAITING = 'SHARE_BAITING'
    TARGETED = 'TARGETED'
    UNKNOWN = 'UNKNOWN'


class MalwareFamily(object):

    """
    Vocabulary for the Malware Family Type.
    """

    AV_SIGNATURE = 'AV_SIGNATURE'
    BARF10 = 'BARF10'
    IMP_HASH = 'IMP_HASH'
    JS004 = 'JS004'
    MANUAL = 'MANUAL'
    RICH_HEADER_HASH = 'RICH_HEADER_HASH'
    SSDEEP_HASH = 'SSDEEP_HASH'
    YARA = 'YARA'


class Precision(object):

    """
    Vocabulary for the Precision Type.
    """

    UNKNOWN = 'UNKNOWN'
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'


class PrivacyType(object):

    """
    Vocabulary for the Threat Indicator Privacy Type.
    """

    VISIBLE = 'VISIBLE'
    HAS_WHITELIST = 'HAS_WHITELIST'


class ReviewStatus(object):

    """
    Vocabulary for the Review Status Type.
    """

    UNKNOWN = 'UNKNOWN'
    UNREVIEWED = 'UNREVIEWED'
    PENDING = 'PENDING'
    REVIEWED_MANUALLY = 'REVIEWED_MANUALLY'
    REVIEWED_AUTOMATICALLY = 'REVIEWED_AUTOMATICALLY'


class Role(object):

    """
    Vocabulary for the Threat Indicator Role type.
    """

    BENEFACTOR = 'BENEFACTOR'
    C2 = 'C2'
    EXPLOIT = 'EXPLOIT'
    RECON = 'RECON'
    PHISHING_SITE = 'PHISHING_SITE'
    TRACKING_PIXEL = 'TRACKING_PIXEL'
    UNKNOWN = 'UNKNOWN'
    WATERING_HOLE = 'WATERING_HOLE'


class Severity(object):

    """
    Vocabulary for the available severity levels for a Threat Indicator.
    """

    INFO = 'INFO'
    WARNING = 'WARNING'
    SUSPICIOUS = 'SUSPICIOUS'
    SEVERE = 'SEVERE'
    APOCALYPSE = 'APOCALYPSE'


class ShareLevel(object):

    """
    Vocabulary for the share level of an object. This is based off of TLP.
    """

    UNKNOWN = 'UNKNOWN'
    WHITE = 'WHITE'
    GREEN = 'GREEN'
    AMBER = 'AMBER'
    RED = 'RED'


class SignatureType(object):

    """
    Vocabulary for the Threat Indicator Signature Threat Type.
    """

    BRO = 'BRO'
    REGEX_URL = 'REGEX_URL'
    SNORT = 'SNORT'
    SURICATA = 'SURICATA'
    YARA = 'YARA'


class Status(object):

    """
    Vocabulary for the status of an object.
    """

    MALICIOUS = 'MALICIOUS'
    NON_MALICIOUS = 'NON_MALICIOUS'
    SUSPICIOUS = 'SUSPICIOUS'
    UNKNOWN = 'UNKNOWN'


class ThreatType(object):

    """
    Vocabulary for the available Threat Types for a Threat Indicator.
    """

    BAD_ACTOR = 'BAD_ACTOR'
    COMPROMISED_CREDENTIAL = 'COMPROMISED_CREDENTIAL'
    COMMAND_EXEC = 'COMMAND_EXEC'
    MALICIOUS_AD = 'MALICIOUS_AD'
    MALICIOUS_API_KEY = 'MALICIOUS_API_KEY'
    MALICIOUS_CONTENT = 'MALICIOUS_CONTENT'
    MALICIOUS_DOMAIN = 'MALICIOUS_DOMAIN'
    MALICIOUS_INJECT = 'MALICIOUS_INJECT'
    MALICIOUS_IP = 'MALICIOUS_IP'
    MALICIOUS_IP_SUBNET = 'MALICIOUS_IP_SUBNET'
    MALICIOUS_URL = 'MALICIOUS_URL'
    MALWARE_ARTIFACTS = 'MALWARE_ARTIFACTS'
    PROXY_IP = 'PROXY_IP'
    SIGNATURE = 'SIGNATURE'
    WEB_REQUEST = 'WEB_REQUEST'
    WHITELIST_DOMAIN = 'WHITELIST_DOMAIN'
    WHITELIST_IP = 'WHITELIST_IP'
    WHITELIST_URL = 'WHITELIST_URL'


class Types(object):

    """
    Vocabulary for the Threat Indicator Types.
    """

    ADJUST_TOKEN = 'ADJUST_TOKEN'
    API_KEY = 'API_KEY'
    AS_NUMBER = 'AS_NUMBER'
    BANNER = 'BANNER'
    CMD_LINE = 'CMD_LINE'
    COOKIE_NAME = 'COOKIE_NAME'
    CRX = 'CRX'
    DEBUG_STRING = 'DEBUG_STRING'
    DEST_PORT = 'DEST_PORT'
    DIRECTORY_QUERIED = 'DIRECTORY_QUERIED'
    DOMAIN = 'DOMAIN'
    EMAIL_ADDRESS = 'EMAIL_ADDRESS'
    FILE_CREATED = 'FILE_CREATED'
    FILE_DELETED = 'FILE_DELETED'
    FILE_MOVED = 'FILE_MOVED'
    FILE_NAME = 'FILE_NAME'
    FILE_OPENED = 'FILE_OPENED'
    FILE_READ = 'FILE_READ'
    FILE_WRITTEN = 'FILE_WRITTEN'
    GET_PARAM = 'GET_PARAM'
    HASH_IMPHASH = 'HASH_IMPHASH'
    HASH_MD5 = 'HASH_MD5'
    HASH_SHA1 = 'HASH_SHA1'
    HASH_SHA256 = 'HASH_SHA256'
    HASH_SSDEEP = 'HASH_SSDEEP'
    HTML_ID = 'HTML_ID'
    HTTP_REQUEST = 'HTTP_REQUEST'
    IP_ADDRESS = 'IP_ADDRESS'
    IP_SUBNET = 'IP_SUBNET'
    ISP = 'ISP'
    LATITUDE = 'LATITUDE'
    LAUNCH_AGENT = 'LAUNCH_AGENT'
    LOCATION = 'LOCATION'
    LONGITUDE = 'LONGITUDE'
    MALWARE_NAME = 'MALWARE_NAME'
    MEMORY_ALLOC = 'MEMORY_ALLOC'
    MEMORY_PROTECT = 'MEMORY_PROTECT'
    MEMORY_WRITTEN = 'MEMORY_WRITTEN'
    MUTANT_CREATED = 'MUTANT_CREATED'
    MUTEX = 'MUTEX'
    NAME_SERVER = 'NAME_SERVER'
    OTHER_FILE_OP = 'OTHER_FILE_OP'
    PASSWORD = 'PASSWORD'
    PASSWORD_SALT = 'PASSWORD_SALT'
    PAYLOAD_DATA = 'PAYLOAD_DATA'
    PAYLOAD_TYPE = 'PAYLOAD_TYPE'
    POST_DATA = 'POST_DATA'
    PROTOCOL = 'PROTOCOL'
    REFERER = 'REFERER'
    REGISTRAR = 'REGISTRAR'
    REGISTRY_KEY = 'REGISTRY_KEY'
    REG_KEY_CREATED = 'REG_KEY_CREATED'
    REG_KEY_DELETED = 'REG_KEY_DELETED'
    REG_KEY_ENUMERATED = 'REG_KEY_ENUMERATED'
    REG_KEY_MONITORED = 'REG_KEY_MONITORED'
    REG_KEY_OPENED = 'REG_KEY_OPENED'
    REG_KEY_VALUE_CREATED = 'REG_KEY_VALUE_CREATED'
    REG_KEY_VALUE_DELETED = 'REG_KEY_VALUE_DELETED'
    REG_KEY_VALUE_MODIFIED = 'REG_KEY_VALUE_MODIFIED'
    REG_KEY_VALUE_QUERIED = 'REG_KEY_VALUE_QUERIED'
    SIGNATURE = 'SIGNATURE'
    SOURCE_PORT = 'SOURCE_PORT'
    TELEPHONE = 'TELEPHONE'
    URI = 'URI'
    USER_AGENT = 'USER_AGENT'
    VOLUME_QUERIED = 'VOLUME_QUERIED'
    WEBSTORAGE_KEY = 'WEBSTORAGE_KEY'
    WEB_PAYLOAD = 'WEB_PAYLOAD'
    WHOIS_NAME = 'WHOIS_NAME'
    WHOIS_ADDR1 = 'WHOIS_ADDR1'
    WHOIS_ADDR2 = 'WHOIS_ADDR2'
    XPI = 'XPI'
