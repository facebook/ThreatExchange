// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.types;

/**
 * Little container for multiple-value method returns in Java.
 */
public class HashesAndQuality {
  public Hash256 hash;
  public Hash256 hashRotate90;
  public Hash256 hashRotate180;
  public Hash256 hashRotate270;
  public Hash256 hashFlipX;
  public Hash256 hashFlipY;
  public Hash256 hashFlipPlus1;
  public Hash256 hashFlipMinus1;
  public int quality;

  public HashesAndQuality(
    Hash256 _hash,
    Hash256 _hashRotate90,
    Hash256 _hashRotate180,
    Hash256 _hashRotate270,
    Hash256 _hashFlipX,
    Hash256 _hashFlipY,
    Hash256 _hashFlipPlus1,
    Hash256 _hashFlipMinus1,
    int _quality)
  {
    this.hash           = _hash; // Note: references not copies
    this.hashRotate90   = _hashRotate90;
    this.hashRotate180  = _hashRotate180;
    this.hashRotate270  = _hashRotate270;
    this.hashFlipX      = _hashFlipX;
    this.hashFlipY      = _hashFlipY;
    this.hashFlipPlus1  = _hashFlipPlus1;
    this.hashFlipMinus1 = _hashFlipMinus1;
    this.quality = _quality;
  }
}
