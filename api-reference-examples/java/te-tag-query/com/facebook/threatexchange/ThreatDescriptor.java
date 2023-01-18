// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package com.facebook.threatexchange;
import java.util.ArrayList;
import java.util.List;

// TEUI CSV-download column names:
// $ mlr --c2x head -n 1 pwny.csv
// td_description          Testing bulk upload
// td_status               NON_MALICIOUS
// td_severity             INFO
// td_share_level          AMBER
// td_review_status        REVIEWED_AUTOMATICALLY
// td_raw_indicator        e8b19da37825a3056e84c522f05eb001
// td_indicator            [object Object]
// td_visibility           HAS_WHITELIST
// td_reactions_by_app
// td_source_uri
// td_reaction_count       0
// td_same_indicator_count 2
// td_related_count        4
// td_creation_time        2019-12-04T15:05:28-05:00
// td_update_time          2019-12-04T15:05:28-05:00
// td_expire_time
// td_first_active
// td_last_active
// td_owner_id             2061458520576715
// td_owner_name           ISE TE Non-MSH Test App
// td_subjective_tags      testing;pwny
// td_whitelist_apps       2061458520576715:ISE TE Non-MSH Test App;494491891138576:Media Hash Sharing RF Test
// td_privacy_groups

// AVAILABLE WITHIN THE GRAPH API, BEING USED:
// * id
// * added_on
// * confidence
// * description -- be sure to escape embedded double-quotes for the JSON.
// * last_updated
// * first_active
// * last_active
// * expired_on
// * owner
// * privacy_type
// * raw_indicator
// * review_status
// * severity
// * share_level
// * status
// * type

// AVAILABLE WITHIN THE GRAPH API, MAYBE USE:
// ? indicator (to get the id ...) -- only useful for relation-edge-following
// ? my_reactions
// ? reactions

/**
 * Helper container class for parsed results back from ThreatExchange.
 */
public class ThreatDescriptor {
  public final String id;
  public final String td_raw_indicator;
  public final String td_indicator_type;
  public final String added_on;
  public final String last_updated;
  public final String td_first_active;
  public final String td_last_active;
  public final String td_expired_on;
  public final String td_confidence;
  public final String td_owner_id;
  public final String td_owner_email;
  public final String td_owner_name;
  public final String td_visibility;
  public final String td_review_status;
  public final String td_status;
  public final String td_severity;
  public final String td_share_level;
  public final List<String> td_subjective_tags;
  public final String td_description;

  public ThreatDescriptor(
    String id_,
    String td_raw_indicator_,
    String td_indicator_type_,
    String added_on_,
    String last_updated_,
    String td_first_active_,
    String td_last_active_,
    String td_expired_on_,
    String td_confidence_,
    String td_owner_id_,
    String td_owner_email_,
    String td_owner_name_,
    String td_visibility_,
    String td_review_status_,
    String td_status_,
    String td_severity_,
    String td_share_level_,
    List<String> td_subjective_tags_,
    String td_description_
  ) {
    id = id_;
    td_raw_indicator = td_raw_indicator_;
    td_indicator_type = td_indicator_type_;
    added_on = added_on_;
    last_updated = last_updated_;
    td_first_active = td_first_active_;
    td_last_active = td_last_active_;
    td_expired_on = td_expired_on_;
    td_confidence = td_confidence_;
    td_owner_id = td_owner_id_;
    td_owner_email = td_owner_email_;
    td_owner_name = td_owner_name_;
    td_visibility = td_visibility_;
    td_review_status = td_review_status_;
    td_status = td_status_;
    td_severity = td_severity_;
    td_share_level = td_share_level_;

    td_subjective_tags = new ArrayList(td_subjective_tags_);
    td_description = td_description_;
  }
}
