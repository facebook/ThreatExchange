package com.facebook.threatexchange;

import java.net.URL;

class Constants {
  public static final String DEFAULT_TE_BASE_URL = "https://graph.facebook.com/v4.0";

  // These are all conventions for hash-sharing over ThreatExchange.
  public static final String HASH_TYPE_PHOTODNA = "HASH_PHOTODNA";
  public static final String HASH_TYPE_PDQ = "HASH_PDQ";
  public static final String HASH_TYPE_MD5 = "HASH_MD5";
  public static final String HASH_TYPE_TMK = "HASH_TMK";

  public static final String THREAT_DESCRIPTOR = "THREAT_DESCRIPTOR";

  public static final String TAG_PREFIX_MEDIA_TYPE = "media_type_";
  public static final String TAG_MEDIA_TYPE_PHOTO = "media_type_photo";
  public static final String TAG_MEDIA_TYPE_VIDEO = "media_type_video";
  public static final String TAG_MEDIA_TYPE_LONG_HASH_VIDEO = "media_type_long_hash_video";

  public static final String TAG_PREFIX_MEDIA_PRIORITY = "media_priority_";
  public static final String TAG_MEDIA_PRIORITY_S0 = "media_priority_s0";
  public static final String TAG_MEDIA_PRIORITY_S1 = "media_priority_s1";
  public static final String TAG_MEDIA_PRIORITY_S2 = "media_priority_s2";
  public static final String TAG_MEDIA_PRIORITY_S3 = "media_priority_s3";
  public static final String TAG_MEDIA_PRIORITY_T0 = "media_priority_t0";
  public static final String TAG_MEDIA_PRIORITY_T1 = "media_priority_t1";
  public static final String TAG_MEDIA_PRIORITY_T2 = "media_priority_t2";
  public static final String TAG_MEDIA_PRIORITY_T3 = "media_priority_t3";
}
