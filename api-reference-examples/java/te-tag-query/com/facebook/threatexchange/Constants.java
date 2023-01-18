// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package com.facebook.threatexchange;

import java.net.URL;

class Constants {
  public static final String DEFAULT_TE_BASE_URL = "https://graph.facebook.com/v6.0";

  // Only used for file-extensions
  public static final String INDICATOR_TYPE_PHOTODNA = "HASH_PHOTODNA";
  public static final String INDICATOR_TYPE_PDQ = "HASH_PDQ";
  public static final String INDICATOR_TYPE_MD5 = "HASH_MD5";
  public static final String INDICATOR_TYPE_TMK = "HASH_TMK";

  public static final String THREAT_DESCRIPTOR = "THREAT_DESCRIPTOR";
}
