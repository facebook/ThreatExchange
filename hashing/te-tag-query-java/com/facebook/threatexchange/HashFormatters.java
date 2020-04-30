// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

package com.facebook.threatexchange;

/**
 * Hash output-formatter
 */
interface HashFormatter {
  public String format(ThreatDescriptor threatDescriptor, boolean printHashString);
}

class JSONHashFormatter implements HashFormatter {
  @Override
  // See also
  // https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-descriptor/v6.0
  public String format(ThreatDescriptor threatDescriptor, boolean printHashString) {
    SimpleJSONWriter w = new SimpleJSONWriter();
    w.add("id", threatDescriptor.id);
    if (printHashString) {
      w.add("td_raw_indicator", threatDescriptor.td_raw_indicator);
    }
    w.add("td_indicator_type", threatDescriptor.td_indicator_type);
    w.add("added_on", threatDescriptor.added_on);
    w.add("last_updated", threatDescriptor.last_updated);
    w.add("td_confidence", threatDescriptor.td_confidence);
    w.add("td_owner_id", threatDescriptor.td_owner_id);
    w.add("td_owner_email", threatDescriptor.td_owner_email);
    w.add("td_owner_name", threatDescriptor.td_owner_name);
    w.add("td_visibility", threatDescriptor.td_visibility);
    w.add("td_review_status", threatDescriptor.td_review_status);
    w.add("td_status", threatDescriptor.td_status);
    w.add("td_severity", threatDescriptor.td_severity);
    w.add("td_share_level", threatDescriptor.td_share_level);
    w.add("td_subjective_tags", String.join(",", threatDescriptor.td_subjective_tags));
    w.add("td_description", threatDescriptor.td_description);
    return w.format();
  }
}
