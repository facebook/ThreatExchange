// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

package com.facebook.threatexchange;

/**
 * Hash output-formatter
 */
interface HashFormatter {
  public String format(SharedHash sharedHash, boolean printHashString);
}

class JSONHashFormatter implements HashFormatter {
  @Override
  public String format(SharedHash sharedHash, boolean printHashString) {
    SimpleJSONWriter w = new SimpleJSONWriter();
    w.add("id", sharedHash.id);
    if (printHashString) {
      w.add("td_raw_indicator", sharedHash.td_raw_indicator);
    }
    w.add("td_indicator_type", sharedHash.td_indicator_type);
    w.add("added_on", sharedHash.added_on);
    w.add("td_confidence", sharedHash.td_confidence);
    w.add("td_owner_id", sharedHash.td_owner_id);
    w.add("td_owner_email", sharedHash.td_owner_email);
    w.add("td_owner_name", sharedHash.td_owner_name);
    w.add("td_visibility", sharedHash.td_visibility);
    w.add("td_status", sharedHash.td_status);
    w.add("td_severity", sharedHash.td_severity);
    w.add("td_share_level", sharedHash.td_share_level);
    w.add("td_subjective_tags", String.join(",", sharedHash.td_subjective_tags));
    return w.format();
  }
}
