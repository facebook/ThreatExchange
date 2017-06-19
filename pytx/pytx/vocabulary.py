class ThreatExchange(object):

    """
    General vocabulary for ThreatExchange.
    """

    URL = 'https://graph.facebook.com/'
    VERSION = 'v2.9/'
    ACCESS_TOKEN = 'access_token'
    DEFAULT_LIMIT = 25

    # GET
    MALWARE_ANALYSES = 'malware_analyses/'
    MALWARE_FAMILIES = 'malware_families/'
    THREAT_EXCHANGE_MEMBERS = 'threat_exchange_members/'
    THREAT_DESCRIPTORS = 'threat_descriptors/'
    THREAT_INDICATORS = 'threat_indicators/'
    THREAT_PRIVACY_GROUPS = 'threat_privacy_groups/'
    THREAT_PRIVACY_GROUPS_MEMBER = 'threat_privacy_groups_member/'
    THREAT_PRIVACY_GROUPS_OWNER = 'threat_privacy_groups_owner/'
    THREAT_TAGS = 'threat_tags/'

    FIELDS = 'fields'
    INCLUDE_EXPIRED = 'include_expired'
    LIMIT = 'limit'
    MAX_CONFIDENCE = 'max_confidence'
    MIN_CONFIDENCE = 'min_confidence'
    OWNER = 'owner'
    REVIEW_STATUS = 'review_status'
    SAMPLE_TYPE = 'sample_type'
    SHARE_LEVEL = 'share_level'
    SINCE = 'since'
    SORT_BY = 'sort_by'
    SORT_ORDER = 'sort_order'
    STATUS = 'status'
    STRICT_TEXT = 'strict_text'
    TEXT = 'text'
    TYPE = 'type'
    UNTIL = 'until'

    DATA = 'data'
    PAGING = 'paging'
    NEXT = 'next'

    ASCENDING = 'ASCENDING'
    CREATE_TIME = 'CREATE_TIME'
    DESCENDING = 'DESCENDING'
    RELEVANCE = 'RELEVANCE'

    METADATA = 'metadata'

    NO_TOTAL = -1
    MIN_TOTAL = 0
    DEC_TOTAL = 1

    # POST
    REACTIONS = 'reactions'
    RELATED = 'related'
    RELATED_ID = 'related_id'

    # BATCH
    BATCH = 'batch'
    INCLUDE_HEADERS = 'include_headers'
    OMIT_RESPONSE_ON_SUCCESS = 'omit_response_on_success'

    # Environment Variables for init()
    TX_ACCESS_TOKEN = 'TX_ACCESS_TOKEN'
    TX_APP_ID = 'TX_APP_ID'
    TX_APP_SECRET = 'TX_APP_SECRET'


class Batch(object):
    """
    Vocabulary used for batch operations.
    """

    METHOD = 'method'
    RELATIVE_URL = 'relative_url'
    BODY = 'body'
    INCLUDE_HEADERS = 'include_headers'


class Common(object):

    """
    Vocabulary common to multiple objects.
    """

    ADDED_ON = 'added_on'
    ID = 'id'
    METADATA = 'metadata'
    MY_REACTIONS = 'my_reactions'
    REVIEW_STATUS = 'review_status'
    SHARE_LEVEL = 'share_level'
    STATUS = 'status'
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
    MEMBERS = 'members'
    RELATED = 'related'
    SIMILAR_MALWARE = 'similar_malware'
    STATUS = Common.STATUS
    TAGGED_OBJECTS = 'tagged_objects'
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
    PRIVACY_TYPE = 'privacy_type'
    REVIEW_STATUS = Common.REVIEW_STATUS
    SAMPLE = 'sample'
    SAMPLE_SIZE = 'sample_size'
    SAMPLE_SIZE_COMPRESSED = 'sample_size_compressed'
    SAMPLE_TYPE = 'sample_type'
    SHA1 = 'sha1'
    SHA256 = 'sha256'
    SHA3_384 = 'sha3_384'
    SHARE_LEVEL = Common.SHARE_LEVEL
    SSDEEP = 'ssdeep'
    STATUS = Common.STATUS
    TAGS = 'tags'
    VICTIM_COUNT = Common.VICTIM_COUNT
    XPI = 'xpi'


class MalwareAnalysisTypes(object):

    """
    Vocabulary specific to Malware Analysis Sample Types
    """

    ANDROID_APK = 'ANDROID_APK'
    CHROME_EXT = 'CHROME_EXT'
    DALVIK_DEX = 'DALVIK_DEX'
    ELF_X64 = 'ELF_X64'
    ELF_X86 = 'ELF_X86'
    FIREFOX_EXT = 'FIREFOX_EXT'
    FLASH_DATA = 'FLASH_DATA'
    FLASH_VIDEO = 'FLASH_VIDEO'
    GENERIC_BINARY = 'GENERIC_BINARY'
    GENERIC_IMAGE = 'GENERIC_IMAGE'
    GENERIC_TEXT = 'GENERIC_TEXT'
    HTML = 'HTML'
    IMAGE_BMP = 'IMAGE_BMP'
    IMAGE_GIF = 'IMAGE_GIF'
    IMAGE_JPEG = 'IMAGE_JPEG'
    IMAGE_PNG = 'IMAGE_PNG'
    IMAGE_TIFF = 'IMAGE_TIFF'
    IOS_APP = 'IOS_APP'
    JAR_ARCHIVE = 'JAR_ARCHIVE'
    JAVASCRIPT = 'JAVASCRIPT'
    MACH_O = 'MACH_O'
    OFFICE_DOCX = 'OFFICE_DOCX'
    OFFICE_PPTX = 'OFFICE_PPTX'
    OFFICE_XLSX = 'OFFICE_XLSX'
    PE_X64 = 'PE_X64'
    PE_X86 = 'PE_X86'
    PDF_DOCUMENT = 'PDF_DOCUMENT'
    RAR_ARCHIVE = 'RAR_ARCHIVE'
    RTF_FILE = 'RTF_FILE'
    UNKNOWN = 'UNKNOWN'
    ZIP_ARCHIVE = 'ZIP_ARCHIVE'


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
    PRIVACY_TYPE = 'privacy_type'
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


class Reaction(object):

    """
    Vocabulary for describing a reaction.
    """

    HELPFUL = 'HELPFUL'
    NOT_HELPFUL = 'NOT_HELPFUL'
    OUTDATED = 'OUTDATED'
    SAW_THIS_TOO = 'SAW_THIS_TOO'
    WANT_MORE_INFO = 'WANT_MORE_INFO'


class Response(object):

    """
    Vocabulary for describing server responses.
    """

    SUCCESS = 'success'
    ID = 'id'
    ERROR = 'error'
    MESSAGE = 'message'
    TYPE = 'type'
    CODE = 'code'
    FBTRACE_ID = 'fbtrace_id'


class ThreatExchangeMember(object):

    """
    Vocabulary for describing a ThreatExchangeMember.
    """

    ID = Common.ID
    NAME = 'name'
    EMAIL = 'email'


class ThreatPrivacyGroup(object):

    """
    Vocabulary for describing a ThreatPrivacyGroup.
    """

    ID = Common.ID
    NAME = 'name'
    DESCRIPTION = 'description'
    MEMBERS = 'members'
    MEMBERS_CAN_SEE = 'members_can_see'
    MEMBERS_CAN_USE = 'members_can_use'


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
    FIRST_ACTIVE = 'first_active'
    ID = Common.ID
    INDICATOR = 'indicator'
    LAST_ACTIVE = 'last_active'
    LAST_UPDATED = 'last_updated'
    METADATA = Common.METADATA
    MY_REACTIONS = Common.MY_REACTIONS
    OWNER = 'owner'
    PRECISION = 'precision'
    PRIVACY_MEMBERS = 'privacy_members'
    PRIVACY_TYPE = 'privacy_type'
    RAW_INDICATOR = 'raw_indicator'
    REVIEW_STATUS = Common.REVIEW_STATUS
    SEVERITY = 'severity'
    SHARE_LEVEL = Common.SHARE_LEVEL
    SOURCE_URI = 'source_uri'
    STATUS = Common.STATUS
    TAGS = 'tags'
    TYPE = 'type'


class ThreatTag(object):

    """
    Vocabulary specific to searching for, adding, or modifying a Threat
    Tag object.
    """

    ID = Common.ID
    NAME = 'name'
    TAGGED_OBJECTS = 'tagged_objects'
    TEXT = 'text'
    TYPE = 'type'


class PopularTags(object):

    """
    Vocabulary which outlines popular tags that are used with ThreatExchange.
    """

    ACCESS_TOKEN_THEFT = 'access_token_theft'
    BAD_ACTOR = 'bad_actor'
    BOGON = 'bogon'
    BOT = 'bot'
    BRUTE_FORCE = 'brute_force'
    CLICKJACKING = 'clickjacking'
    COMPROMISED = 'compromised'
    COMPROMISED_CREDENTIAL = 'compromised_credential'
    CREEPER = 'creeper'
    DRUGS = 'drugs'
    EMAIL_SPAM = 'email_spam'
    EXPLICIT_CONTENT = 'explicit_content'
    EXPLOIT_KIT = 'exploit_kit'
    FAKE_ACCOUNT = 'fake_account'
    FINANCIAL = 'financial'
    HT_VICTIM = 'ht_victim'
    IP_INFRINGEMENT = 'ip_infringement'
    MALICIOUS_AD = 'malicious_ad'
    MALICIOUS_API_KEY = 'malicious_api_key'
    MALICIOUS_APP = 'malicious_app'
    MALICIOUS_CONTENT = 'malicious_content'
    MALICIOUS_DOMAIN = 'malicious_domain'
    MALICIOUS_INJECT = 'malicious_inject'
    MALICIOUS_IP = 'malicious_ip'
    MALICIOUS_NAMESERVER = 'malicious_nameserver'
    MALICIOUS_SUBNET = 'malicious_subnet'
    MALICIOUS_SSL_CERT = 'malicious_ssl_cert'
    MALICIOUS_WEBSERVER = 'malicious_webserver'
    MALWARE_SAMPLE = 'malware_sample'
    MALWARE_VICTIM = 'malware_victim'
    MALVERTISING = 'malvertising'
    MALWARE = 'malware'
    PASSIVE_DNS = 'passive_dns'
    PHISHING = 'phishing'
    PIRACY = 'piracy'
    PROXY = 'proxy'
    PROXY_IP = 'proxy_ip'
    SCAM = 'scam'
    SCANNING = 'scanning'
    SCRAPING = 'scraping'
    SELF_XSS = 'self_xss'
    SHARE_BAITING = 'share_baiting'
    SIGNATURE = 'signature'
    TARGETED = 'targeted'
    TERRORISM = 'terrorism'
    WEAPONS = 'weapons'
    WEB_APP = 'web_app'
    WEB_REQUEST = 'web_request'
    WHITELIST_DOMAIN = 'whitelist_domain'
    WHITELIST_IP = 'whitelist_ip'
    WHITELIST_URL = 'whitelist_url'


class MalwareFamily(object):

    """
    Vocabulary for the Malware Family Type.
    """

    AVSCAN = 'AVSCAN'
    AV_SIGNATURE = 'AV_SIGNATURE'
    BARF10 = 'BARF10'
    FSH_HTML = 'FSH_HTML'
    FSH_SSDEEP = 'FSH_SSDEEP'
    IMP_HASH = 'IMP_HASH'
    JS004 = 'JS004'
    JS005 = 'JS005'
    MANUAL = 'MANUAL'
    PE_CERT_SHA256 = 'PE_CERT_SHA256'
    PE_EXPORT = 'PE_EXPORT'
    PE_RSRC_SHA256 = 'PE_RSRC_SHA256'
    PE_SECTION_SHA256 = 'PE_SECTION_SHA256'
    PE_TIMESTAMP = 'PE_TIMESTAMP'
    PE_VERSION_VALUE = 'PE_VERSION_VALUE'
    RICH_HEADER_HASH = 'RICH_HEADER_HASH'
    SSDEEP_HASH = 'SSDEEP_HASH'
    UNKNOWN = 'UNKNOWN'
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

    HAS_PRIVACY_GROUP = 'HAS_PRIVACY_GROUP'
    HAS_WHITELIST = 'HAS_WHITELIST'
    NONE = 'NONE'
    VISIBLE = 'VISIBLE'


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
    Intentionally out of alphabetical order to reflect order of severity.
    """

    UNKNOWN = 'UNKNOWN'
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
    UNKNOWN = 'UNKNOWN'
    YARA = 'YARA'


class Status(object):

    """
    Vocabulary for the status of an object.
    """

    MALICIOUS = 'MALICIOUS'
    NON_MALICIOUS = 'NON_MALICIOUS'
    SUSPICIOUS = 'SUSPICIOUS'
    UNKNOWN = 'UNKNOWN'


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
