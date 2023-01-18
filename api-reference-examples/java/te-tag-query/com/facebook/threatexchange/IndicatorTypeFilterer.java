// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package com.facebook.threatexchange;

import java.io.PrintStream;
import java.util.stream.Stream;
import java.util.Map;
import java.util.HashMap;

class IndicatorTypeFilterer {
  private String _uppercaseName;
  private String _lowercaseName;

  // The uppercase names are the ones coming back in the 'type' field in TE API
  // requests. The lowercase names are standard shorthands.
  //
  // Note: this data structure Could be a hashmap-literal but the syntax gets
  // neater in Java 9 & let's keep this code backward-compatible with various
  // Java versions.
  private static final String[][] NAMES = {
    {"ADJUST_TOKEN", "adjustToken"},
    {"API_KEY", "api_key"},
    {"AS_NUMBER", "asn"},
    {"BANNER", "banner"},
    {"CMD_LINE", "cmd_line"},
    {"COOKIE_NAME", "cookie"},
    {"CRX", "crx"},
    {"DEBUG_STRING", "dbgstr"},
    {"DEBUG_STRING", "debug_string"},
    {"DEST_PORT", "dst_port"},
    {"DIRECTORY_QUERIED", "directoryQueried"},
    {"DOMAIN", "domain"},
    {"EMAIL_ADDRESS", "email"},
    {"FILE_CREATED", "fileCreated"},
    {"FILE_DELETED", "fileDeleted"},
    {"FILE_MOVED", "fileMoved"},
    {"FILE_NAME", "file_name"},
    {"FILE_OPENED", "fileOpened"},
    {"FILE_READ", "fileRead"},
    {"FILE_WRITTEN", "fileWritten"},
    {"GET_PARAM", "get_param"},
    {"HASH_IMPHASH", "imphash"},
    {"HASH_SSDEEP", "ssdeep"},
    {"HASH_PHOTODNA", "photodna"},
    {"HASH_PDQ", "pdq"},
    {"HASH_MD5", "md5"},
    {"HASH_TMK", "tmk"},
    {"HASH_SHA1", "sha1"},
    {"HASH_SHA256", "sha256"},
    {"HTML_ID", "htmlid"},
    {"HTTP_REQUEST", "http_req"},
    {"IP_ADDRESS", "ip"},
    {"IP_SUBNET", "subnet"},
    {"ISP", "isp"},
    {"LATITUDE", "lat"},
    {"LAUNCH_AGENT", "launch_agent"},
    {"LOCATION", "location"},
    {"LONGITUDE", "long"},
    {"MALWARE_NAME", "malware"},
    {"MEMORY_ALLOC", "memAlloc"},
    {"MEMORY_PROTECT", "memProtect"},
    {"MEMORY_WRITTEN", "memWritten"},
    {"MUTANT_CREATED", "mutantCreated"},
    {"MUTEX", "mutex"},
    {"NAME_SERVER", "ns"},
    {"OTHER_FILE_OP", "fileOtherOp"},
    {"PASSWORD", "password"},
    {"PASSWORD_SALT", "salt"},
    {"PAYLOAD_DATA", "payload_data"},
    {"POST_DATA", "post_data"},
    {"PROTOCOL", "proto"},
    {"REFERER", "referer"},
    {"REGISTRAR", "registrar"},
    {"REGISTRY_KEY", "regkey"},
    {"REG_KEY_CREATED", "keyCreated"},
    {"REG_KEY_DELETED", "keyDeleted"},
    {"REG_KEY_ENUMERATED", "keyEnumerated"},
    {"REG_KEY_MONITORED", "keyMonitored"},
    {"REG_KEY_OPENED", "keyOpened"},
    {"REG_KEY_VALUE_CREATED", "keyValueCreated"},
    {"REG_KEY_VALUE_DELETED", "keyValueDeleted"},
    {"REG_KEY_VALUE_MODIFIED", "keyValueModified"},
    {"REG_KEY_VALUE_QUERIED", "keyValueQueried"},
    {"SIGNATURE", "signature"},
    {"SOURCE_PORT", "src_prt"},
    {"TELEPHONE", "telnum"},
    {"URI", "uri"},
    {"USER_AGENT", "ua"},
    {"VOLUME_QUERIED", "volumeInformationQueried"},
    {"WEBSTORAGE_KEY", "webstorkey"},
    {"WEB_PAYLOAD", "webpayload"},
    {"WHOIS_NAME", "whois_name"},
    {"WHOIS_ADDR1", "whois_addr1"},
    {"WHOIS_ADDR2", "whois_addr2"},
    {"XPI", "xpi"}
  };

  // Private constructor; factory methods are public.
  private IndicatorTypeFilterer(String uppercaseName, String lowercaseName) {
    this._uppercaseName = uppercaseName;
    this._lowercaseName = lowercaseName;
  }

  public static void list(PrintStream o) {
    int n = NAMES.length;
    o.printf("Indicator-type filters:\n");
    for (int i = 0; i < n; i++) {
      String uppercaseName = NAMES[i][0];
      String lowercaseName = NAMES[i][1];
      o.printf("%-25s or %s\n", uppercaseName, lowercaseName);
    }
  }

  public static IndicatorTypeFilterer createAllFilterer() {
      return new IndicatorTypeFilterer(null, null);
  }

  public static IndicatorTypeFilterer create(String name) {
    int n = NAMES.length;
    for (int i = 0; i < n; i++) {
      String uppercaseName = NAMES[i][0];
      String lowercaseName = NAMES[i][1];
      if (name.equals(uppercaseName) || name.equals(lowercaseName)) {
        return new IndicatorTypeFilterer(uppercaseName, lowercaseName);
      }
    }
    return null;
  }

  public boolean accept(String indicatorType) {
    if (this._uppercaseName == null) {
      return true;
    } else {
      return indicatorType.equals(this._uppercaseName);
    }
  }

  // The 'type' field coming back from TE API requests has 'HASH_MD5' not
  // 'md5', etc.
  public String getUppercaseName() {
    return this._uppercaseName;
  }
}
