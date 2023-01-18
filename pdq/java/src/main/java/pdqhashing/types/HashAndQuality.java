// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.types;

/**
 * Little container for multiple-value method returns in Java.
 */
public class HashAndQuality {
  private Hash256 hash;
  private int quality;
  public HashAndQuality(Hash256 _hash, int _quality) {
    this.hash = _hash; // Note: reference not copy
    this.quality = _quality;
  }
  public Hash256 getHash() {
    return this.hash;
  }
  public int getQuality() {
    return this.quality;
  }
}
