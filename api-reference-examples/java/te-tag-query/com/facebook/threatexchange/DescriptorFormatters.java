// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package com.facebook.threatexchange;

/**
 * Descriptor output-formatter
 */
interface DescriptorFormatter {
  public String format(ThreatDescriptor threatDescriptor, boolean includeIndicatorInOutput);
}

class JSONDescriptorFormatter implements DescriptorFormatter {
  @Override
  // See also
  // https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-descriptor/v6.0
  public String format(ThreatDescriptor threatDescriptor, boolean includeIndicatorInOutput) {
    SimpleJSONWriter w = new SimpleJSONWriter();
    w.add("id", threatDescriptor.id);
    if (includeIndicatorInOutput) {
      w.add("td_raw_indicator", threatDescriptor.td_raw_indicator);
    }
    w.add("td_indicator_type", threatDescriptor.td_indicator_type);
    w.add("added_on", threatDescriptor.added_on);
    w.add("last_updated", threatDescriptor.last_updated);
    w.ifValudNotNullAdd("td_first_active", threatDescriptor.td_first_active);
    w.ifValudNotNullAdd("td_last_active", threatDescriptor.td_last_active);
    w.ifValudNotNullAdd("td_expired_on", threatDescriptor.td_expired_on);
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
