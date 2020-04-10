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
    w.add("hash_id", sharedHash.hashID);
    if (printHashString) {
      w.add("hash_value", sharedHash.hashValue);
    }
    w.add("hash_type", sharedHash.hashType);
    w.add("added_on", sharedHash.addedOn);
    w.add("confidence", sharedHash.confidence);
    w.add("owner_id", sharedHash.ownerID);
    w.add("owner_email", sharedHash.ownerEmail);
    w.add("owner_name", sharedHash.ownerName);
    w.add("tags", String.join(",", sharedHash.tags));
    return w.format();
  }
}
