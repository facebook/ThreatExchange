// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.types;

import pdqhashing.types.Hash256;

/**
 * Container for MIH queries
 */
public class Hash256AndMetadata<Metadata> {
  public final Hash256 hash;
  public final Metadata metadata;
  public Hash256AndMetadata(Hash256 hash_, Metadata metadata_) {
    this.hash = hash_;
    this.metadata = metadata_;
  }
}
