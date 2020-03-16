// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
var v_ThreatExchange = {
    URL             : "https://graph.facebook.com/",
    VERSION         : "v2.4/",
    ACCESS_TOKEN    : "access_token",
    DEFAULT_LIMIT   : 500,
    MAX_LIMIT       : 5000,
    MALWARE_ANALYSES        : "malware_analyses/",
    MALWARE_FAMILIES        : "malware_families/",
    THREAT_EXCHANGE_MEMBERS : "threat_exchange_members/",
    THREAT_DESCRIPTORS      : "threat_descriptors/",
    THREAT_INDICATORS       : "threat_indicators/",
    LIMIT       : "limit",
    TEXT        : "text",
    STRICT_TEXT : "strict_text",
    SINCE       : "since",
    UNTIL       : "until",
    TYPE        : "type",
    THREAT_TYPE : "threat_type",
    FIELDS      : "fields",
    DATA        : "data",
    PAGING      : "paging",
    NEXT        : "next",
    OWNER       : "owner",
    METADATA    : "metadata",
    NO_TOTAL    : -1,
    MIN_TOTAL   : 0,
    DEC_TOTAL   : 1,
    RELATED     : "related/",
    RELATED_ID  : "related_id",
}

var v_Common = {
    ADDED_ON        : "added_on",
    ID              : "id",
    METADATA        : "metadata",
    SHARE_LEVEL     : "share_level",
    STATUS          : "status",
    SUBMITTER_COUNT : "submitter_count",
    VICTIM_COUNT    : "victim_count",
}

var v_Connection = {
    ADDED_ON            : v_Common.ADDED_ON,
    CRX                 : "crx",
    DESCRIPTORS         : "descriptors",
    DROPPED             : "dropped",
    DROPPED_BY          : "dropped_by",
    FAMILIES            : "families",
    ID                  : v_Common.ID,
    MALWARE_ANALYSES    : "malware_analyses",
    RELATED             : "related",
    STATUS              : v_Common.STATUS,
    THREAT_INDICATORS   : "threat_indicators",
    VARIANTS            : "variants",
    VICTIM_COUNT        : v_Common.VICTIM_COUNT,
}

var v_Malware = {
    ADDED_ON        : v_Common.ADDED_ON,
    CRX             : "crx",
    ID              : v_Common.ID,
    IMPHASH         : "imphash",
    MD5             : "md5",
    METADATA        : v_Common.METADATA,
    PASSWORD        : "password",
    PE_RICH_HEADER  : "pe_rich_header",
    SAMPLE          : "sample",
    SHA1            : "sha1",
    SHA256          : "sha256",
    SHARE_LEVEL     : v_Common.SHARE_LEVEL,
    SSDEEP          : "ssdeep",
    STATUS          : v_Common.STATUS,
    SUBMITTER_COUNT : v_Common.SUBMITTER_COUNT,
    VICTIM_COUNT    : v_Common.VICTIM_COUNT,
    XPI             : "xpi",
}

var v_MalwareFamilies = {
    ADDED_ON        : v_Common.ADDED_ON,
    ALIASES         : "aliases",
    DESCRIPTION     : "description",
    FAMILY_TYPE     : "family_type",
    ID              : v_Common.ID,
    MALICIOUS       : "malicious",
    NAME            : "name",
    SAMPLE_COUNT    : "sample_count",
    SHARE_LEVEL     : v_Common.SHARE_LEVEL,
}

var v_Paging = {
    PAGING  : "paging",
    CURSORS : "cursors",
    NEXT    : "next",
}

var v_PagingCursor = {
    BEFORE  : "before",
    AFTER   : "after",
}

var v_Response = {
    SUCCESS : "success",
    ID      : "id",
}

var v_ThreatExchangeMember = {
    ID      : v_Common.ID,
    NAME    : "name",
    EMAIL   : "email",
}

var v_ThreatDescriptor = {
    ADDED_ON        : v_Common.ADDED_ON,
    CONFIDENCE      : "confidence",
    DESCRIPTION     : "description",
    EXPIRED_ON      : "expired_on",
    ID              : v_Common.ID,
    INDICATOR       : "indicator",
    LAST_UPDATED    : "last_updated",
    METADATA        : v_Common.METADATA,
    OWNER           : "owner",
    PRECISION       : "precision",
    PRIVACY_MEMBERS : "privacy_members",
    PRIVACY_TYPE    : "privacy_type",
    RAW_INDICATOR   : "raw_indicator",
    REVIEW_STATUS   : "review_status",
    SEVERITY        : "severity",
    SHARE_LEVEL     : v_Common.SHARE_LEVEL,
    STATUS          : v_Common.STATUS,
    SUBMITTER_COUNT : v_Common.SUBMITTER_COUNT,
    THREAT_TYPE     : "threat_type",
    THREAT_TYPES    : "threat_types",
    TYPE            : "type",
}

var v_ThreatIndicator = {
    ID              : v_Common.ID,
    INDICATOR       : "indicator",
    METADATA        : v_Common.METADATA,
    TYPE            : "type",
}

var v_MalwareFamily = {
    AV_SIGNATURE     : "AV_SIGNATURE",
    BARF10           : "BARF10",
    IMP_HASH         : "IMP_HASH",
    JS004            : "JS004",
    MANUAL           : "MANUAL",
    RICH_HEADER_HASH : "RICH_HEADER_HASH",
    SSDEEP_HASH      : "SSDEEP_HASH",
    YARA             : "YARA",
}

var v_Precision = {
    UNKNOWN : "UNKNOWN",
    LOW     : "LOW",
    MEDIUM  : "MEDIUM",
    HIGH    : "HIGH",
}

var v_ReviewStatus = {
    UNKNOWN                : "UNKNOWN",
    UNREVIEWED             : "UNREVIEWED",
    PENDING                : "PENDING",
    REVIEWED_MANUALLY      : "REVIEWED_MANUALLY",
    REVIEWED_AUTOMATICALLY : "REVIEWED_AUTOMATICALLY",
}

var v_ThreatType = {
    BAD_ACTOR               : "BAD_ACTOR",
    COMPROMISED_CREDENTIAL  : "COMPROMISED_CREDENTIAL",
    COMMAND_EXEC            : "COMMAND_EXEC",
    MALICIOUS_AD            : "MALICIOUS_AD",
    MALICIOUS_API_KEY       : "MALICIOUS_API_KEY",
    MALICIOUS_CONTENT       : "MALICIOUS_CONTENT",
    MALICIOUS_DOMAIN        : "MALICIOUS_DOMAIN",
    MALICIOUS_INJECT        : "MALICIOUS_INJECT",
    MALICIOUS_IP            : "MALICIOUS_IP",
    MALICIOUS_IP_SUBNET     : "MALICIOUS_IP_SUBNET",
    MALICIOUS_URL           : "MALICIOUS_URL",
    MALWARE_ARTIFACTS       : "MALWARE_ARTIFACTS",
    PROXY_IP                : "PROXY_IP",
    SIGNATURE               : "SIGNATURE",
    WEB_REQUEST             : "WEB_REQUEST",
    WHITELIST_DOMAIN        : "WHITELIST_DOMAIN",
    WHITELIST_IP            : "WHITELIST_IP",
    WHITELIST_URL           : "WHITELIST_URL",
}

var v_Severity = {
    INFO        : "INFO",
    WARNING     : "WARNING",
    SUSPICIOUS  : "SUSPICIOUS",
    SEVERE      : "SEVERE",
    APOCALYPSE  : "APOCALYPSE",
}

var v_ShareLevel = {
    UNKNOWN : "UNKNOWN",
    WHITE   : "WHITE",
    GREEN   : "GREEN",
    AMBER   : "AMBER",
    RED     : "RED",
}

var v_Status = {
    MALICIOUS       : "MALICIOUS",
    NON_MALICIOUS   : "NON_MALICIOUS",
    SUSPICIOUS      : "SUSPICIOUS",
    UNKNOWN         : "UNKNOWN",
}

var v_Attack = {
    ACCESS_TOKEN_THEFT  : "ACCESS_TOKEN_THEFT",
    BRUTE_FORCE         : "BRUTE_FORCE",
    CLICKJACKING        : "CLICKJACKING",
    EMAIL_SPAM          : "EMAIL_SPAM",
    FAKE_ACCOUNTS       : "FAKE_ACCOUNTS",
    IP_INFRINGEMENT     : "IP_INFRINGEMENT",
    MALICIOUS_APP       : "MALICIOUS_APP",
    MALWARE             : "MALWARE",
    PHISHING            : "PHISHING",
    SELF_XSS            : "SELF_XSS",
    SHARE_BAITING       : "SHARE_BAITING",
    TARGETED            : "TARGETED",
    UNKNOWN             : "UNKNOWN",
}

var v_PrivacyType = {
    VISIBLE         : "VISIBLE",
    HAS_WHITELIST    : "HAS_WHITELIST",
}

var v_Role = {
    BENEFACTOR      : "BENEFACTOR",
    C2              : "C2",
    EXPLOIT         : "EXPLOIT",
    RECON           : "RECON",
    PHISHING_SITE   : "PHISHING_SITE",
    TRACKING_PIXEL  : "TRACKING_PIXEL",
    UNKNOWN         : "UNKNOWN",
    WATERING_HOLE   : "WATERING_HOLE",
}

var v_SignatureType = {
    BRO         : "BRO",
    REGEX_URL   : "REGEX_URL",
    SNORT       : "SNORT",
    SURICATA    : "SURICATA",
    YARA        : "YARA",
}

var v_Types = {
    ADJUST_TOKEN            : "ADJUST_TOKEN",
    API_KEY                 : "API_KEY",
    AS_NUMBER               : "AS_NUMBER",
    BANNER                  : "BANNER",
    CMD_LINE                : "CMD_LINE",
    COOKIE_NAME             : "COOKIE_NAME",
    CRX                     : "CRX",
    DEBUG_STRING            : "DEBUG_STRING",
    DEST_PORT               : "DEST_PORT",
    DIRECTORY_QUERIED       : "DIRECTORY_QUERIED",
    DOMAIN                  : "DOMAIN",
    EMAIL_ADDRESS           : "EMAIL_ADDRESS",
    FILE_CREATED            : "FILE_CREATED",
    FILE_DELETED            : "FILE_DELETED",
    FILE_MOVED              : "FILE_MOVED",
    FILE_NAME               : "FILE_NAME",
    FILE_OPENED             : "FILE_OPENED",
    FILE_READ               : "FILE_READ",
    FILE_WRITTEN            : "FILE_WRITTEN",
    GET_PARAM               : "GET_PARAM",
    HASH_IMPHASH            : "HASH_IMPHASH",
    HASH_MD5                : "HASH_MD5",
    HASH_SHA1               : "HASH_SHA1",
    HASH_SHA256             : "HASH_SHA256",
    HASH_SSDEEP             : "HASH_SSDEEP",
    HTML_ID                 : "HTML_ID",
    HTTP_REQUEST            : "HTTP_REQUEST",
    IP_ADDRESS              : "IP_ADDRESS",
    IP_SUBNET               : "IP_SUBNET",
    ISP                     : "ISP",
    LATITUDE                : "LATITUDE",
    LAUNCH_AGENT            : "LAUNCH_AGENT",
    LOCATION                : "LOCATION",
    LONGITUDE               : "LONGITUDE",
    MALWARE_NAME            : "MALWARE_NAME",
    MEMORY_ALLOC            : "MEMORY_ALLOC",
    MEMORY_PROTECT          : "MEMORY_PROTECT",
    MEMORY_READ             : "MEMORY_READ",
    MEMORY_WRITTEN          : "MEMORY_WRITTEN",
    MUTANT_CREATED          : "MUTANT_CREATED",
    MUTEX                   : "MUTEX",
    NAME_SERVER             : "NAME_SERVER",
    OTHER_FILE_OP           : "OTHER_FILE_OP",
    PASSWORD                : "PASSWORD",
    PASSWORD_SALT           : "PASSWORD_SALT",
    PAYLOAD_DATA            : "PAYLOAD_DATA",
    PAYLOAD_TYPE            : "PAYLOAD_TYPE",
    POST_DATA               : "POST_DATA",
    PROTOCOL                : "PROTOCOL",
    REFERER                 : "REFERER",
    REGISTRAR               : "REGISTRAR",
    REGISTRY_KEY            : "REGISTRY_KEY",
    REG_KEY_CREATED         : "REG_KEY_CREATED",
    REG_KEY_DELETED         : "REG_KEY_DELETED",
    REG_KEY_ENUMERATED      : "REG_KEY_ENUMERATED",
    REG_KEY_MONITORED       : "REG_KEY_MONITORED",
    REG_KEY_OPENED          : "REG_KEY_OPENED",
    REG_KEY_VALUE_CREATED   : "REG_KEY_VALUE_CREATED",
    REG_KEY_VALUE_DELETED   : "REG_KEY_VALUE_DELETED",
    REG_KEY_VALUE_MODIFIED  : "REG_KEY_VALUE_MODIFIED",
    REG_KEY_VALUE_QUERIED   : "REG_KEY_VALUE_QUERIED",
    SIGNATURE               : "SIGNATURE",
    SOURCE_PORT             : "SOURCE_PORT",
    TELEPHONE               : "TELEPHONE",
    URI                     : "URI",
    USER_AGENT              : "USER_AGENT",
    VOLUME_QUERIED          : "VOLUME_QUERIED",
    WEBSTORAGE_KEY          : "WEBSTORAGE_KEY",
    WEB_PAYLOAD             : "WEB_PAYLOAD",
    WHOIS_NAME              : "WHOIS_NAME",
    WHOIS_ADDR1             : "WHOIS_ADDR1",
    WHOIS_ADDR2             : "WHOIS_ADDR2",
    XPI                     : "XPI",
}
