// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

package com.facebook.threatexchange;
import java.util.ArrayList;
import java.util.List;

/**
 * Helper container class for parsed results back from ThreatExchange.
 */
public class SharedHash {
  public final String hashID;
  public final String hashValue;
  public final String hashType;
  public final String addedOn;
  public final String confidence;
  public final String ownerID;
  public final String ownerEmail;
  public final String ownerName;
  public final List<String> tags;

  public SharedHash(
    String hashID_,
    String hashValue_,
    String hashType_,
    String addedOn_,
    String confidence_,
    String ownerID_,
    String ownerEmail_,
    String ownerName_,
    List<String> tags_
  ) {
    hashID = hashID_;
    hashValue = hashValue_;
    hashType = hashType_;
    addedOn = addedOn_;
    confidence = confidence_;
    ownerID = ownerID_;
    ownerEmail = ownerEmail_;
    ownerName = ownerName_;
    tags = new ArrayList(tags_);
  }
}
