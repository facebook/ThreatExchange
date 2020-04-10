// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

package com.facebook.threatexchange;

import java.net.URL;

class Constants {
  public static final String DEFAULT_TE_BASE_URL = "https://graph.facebook.com/v4.0";

  // These are all conventions for hash-sharing over ThreatExchange.
  public static final String INDICATOR_TYPE_PHOTODNA = "HASH_PHOTODNA";
  public static final String INDICATOR_TYPE_PDQ = "HASH_PDQ";
  public static final String INDICATOR_TYPE_MD5 = "HASH_MD5";
  public static final String INDICATOR_TYPE_TMK = "HASH_TMK";

  public static final String THREAT_DESCRIPTOR = "THREAT_DESCRIPTOR";
}
