// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.types;

import pdqhashing.types.PDQHashFormatException;
import java.io.PrintStream;
import java.util.Arrays;
import java.util.Random;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 256-bit hashes with Hamming distance
 */
public class Hash256 implements Comparable<Hash256> {
  public static final int HASH256_NUM_SLOTS = 16;

  private static final String IO_FORMAT =
    "%04x%04x%04x%04x%04x%04x%04x%04x%04x%04x%04x%04x%04x%04x%04x%04x";

  private static final Pattern HEX_PATTERN = Pattern.compile(
    "([0-9a-fA-F]{4})([0-9a-fA-F]{4})([0-9a-fA-F]{4})([0-9a-fA-F]{4})" +
    "([0-9a-fA-F]{4})([0-9a-fA-F]{4})([0-9a-fA-F]{4})([0-9a-fA-F]{4})" +
    "([0-9a-fA-F]{4})([0-9a-fA-F]{4})([0-9a-fA-F]{4})([0-9a-fA-F]{4})" +
    "([0-9a-fA-F]{4})([0-9a-fA-F]{4})([0-9a-fA-F]{4})([0-9a-fA-F]{4})"
  );

  private static final Random RNG = new Random(); // for the fuzz() method

  // 16 slots of 16 bits each. See ../README.md for why not 8x32 or 32x8, etc.
  public final short[] w;

  // ----------------------------------------------------------------
  public Hash256() {
    this.w = new short[HASH256_NUM_SLOTS];
    for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
      this.w[i] = 0;
    }
  }

  // ----------------------------------------------------------------
  public Hash256 clone() {
    Hash256 rv = new Hash256();
    for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
      rv.w[i] = this.w[i];
    }
    return rv;
  }

  // ----------------------------------------------------------------
  public int getNumWords() {
    return HASH256_NUM_SLOTS;
  }

  // ----------------------------------------------------------------
  @Override
  public String toString() {
    return String.format(IO_FORMAT,
      (int)(this.w[15] & 0xffff), (int)(this.w[14] & 0xffff),
      (int)(this.w[13] & 0xffff), (int)(this.w[12] & 0xffff),
      (int)(this.w[11] & 0xffff), (int)(this.w[10] & 0xffff),
      (int)(this.w[9]  & 0xffff), (int)(this.w[8]  & 0xffff),
      (int)(this.w[7]  & 0xffff), (int)(this.w[6]  & 0xffff),
      (int)(this.w[5]  & 0xffff), (int)(this.w[4]  & 0xffff),
      (int)(this.w[3]  & 0xffff), (int)(this.w[2]  & 0xffff),
      (int)(this.w[1]  & 0xffff), (int)(this.w[0]  & 0xffff));
  }

  // ----------------------------------------------------------------
  public static Hash256 fromHexString(String s)
    throws PDQHashFormatException
  {
    Hash256 rv = new Hash256();

    Matcher matcher = HEX_PATTERN.matcher(s);
    if (matcher.find()) {
      for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
        String group = matcher.group(16 - i); // 1-up and reversed
        rv.w[i] = (short)(int)Integer.valueOf(group, 16);
      }
    } else {
      throw new PDQHashFormatException(s);
    }

    return rv;
  }

  // ----------------------------------------------------------------
  public static int hammingNorm16(short h) {
    return Integer.bitCount(((int)h) & 0xffff);
  }

  public void clearAll() {
    for (int i = 0; i < HASH256_NUM_SLOTS; i++)
      this.w[i] = 0;
  }

  public void setAll() {
    for (int i = 0; i < HASH256_NUM_SLOTS; i++)
      this.w[i] = ~0;
  }

  public int hammingNorm() {
    int n = 0;
    for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
      n += hammingNorm16(this.w[i]);
    }
    return n;
  }

  public int hammingDistance(Hash256 that) {
    int n = 0;
    for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
      n += hammingNorm16((short)(this.w[i] ^ that.w[i]));
    }
    return n;
  }

  public boolean hammingDistanceLE(Hash256 that, int d) {
    int e = 0;
    for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
      e += hammingNorm16((short)(this.w[i] ^ that.w[i]));
      if (e > d)
        return false;
    }
    return true;
  }

  public void setBit(int k) {
    this.w[(k & 255) >> 4] |= 1 << (k & 15);
  }

  public void flipBit(int k) {
    this.w[(k & 255) >> 4] ^= 1 << (k & 15);
  }

  public Hash256 bitwiseXOR(Hash256 that) {
    Hash256 rv = new Hash256();
    for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
      rv.w[i] = (short)(this.w[i] ^ that.w[i]);
    }
    return rv;
  }

  public Hash256 bitwiseAND(Hash256 that) {
    Hash256 rv = new Hash256();
    for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
      rv.w[i] = (short)(this.w[i] & that.w[i]);
    }
    return rv;
  }

  public Hash256 bitwiseOR(Hash256 that) {
    Hash256 rv = new Hash256();
    for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
      rv.w[i] = (short)(this.w[i] | that.w[i]);
    }
    return rv;
  }

  public Hash256 bitwiseNOT() {
    Hash256 rv = new Hash256();
    for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
      rv.w[i] = (short)(~ this.w[i]);
    }
    return rv;
  }

  public void dumpBits(PrintStream o) {
    for (int i = HASH256_NUM_SLOTS - 1; i >= 0; i--) {
      int word = ((int)this.w[i]) & 0xffff;
      for (int j = 15; j >= 0; j--) {
        if ((word & (1 << j)) != 0) {
          o.printf(" 1");
        } else {
          o.printf(" 0");
        }
      }
      o.printf("\n");
    }
    o.printf("\n");
  }

  public void dumpBitsAcross(PrintStream o) {
    for (int i = HASH256_NUM_SLOTS - 1; i >= 0; i--) {
      int word = ((int)this.w[i]) & 0xffff;
      for (int j = 15; j >= 0; j--) {
        if ((word & (1 << j)) != 0) {
          o.printf(" 1");
        } else {
          o.printf(" 0");
        }
      }
    }
    o.printf("\n");
  }

  public void dumpWords(PrintStream o) {
    for (int i = HASH256_NUM_SLOTS - 1; i >= 0; i--) {
      short word = this.w[i];
      if (i < HASH256_NUM_SLOTS - 1)
        o.printf(" ");
      o.printf("%04x", ((int)word) & 0xffff);
    }
    o.printf("\n");
  }

  // Helper method to do sign extension
  private int toWord(short w) {
    return (int)w & 0xffff;
  }

  public void dumpInt64Vals(PrintStream o) {
    for (int i = HASH256_NUM_SLOTS - 1; i >= 0;) {
      long val = toWord(this.w[i--]);
      val = (val << 16) ^ toWord(this.w[i--]);
      val = (val << 16) ^ toWord(this.w[i--]);
      val = (val << 16) ^ toWord(this.w[i--]);
      o.printf("%d", val);
      if (i >= 0)
        o.printf(" ");
    }
    o.printf("\n");
  }

  /**
   * Flips some number of bits randomly, with replacement.  (I.e. not all
   * flipped bits are guaranteed to be in different positions; if you pass
   * argument of 10 then maybe 2 bits will be flipped and flipped back, and
   * only 6 flipped once.)
   */
  public Hash256 fuzz(int numErrorBits) {
    Hash256 rv = this.clone();
    for (int i = 0; i < numErrorBits; i++) {
      rv.flipBit(RNG.nextInt(256));
    }
    return rv;
  }

  // ================================================================
  // For Java collections: so we can make hashmaps of PDQ hashes, and so on.

  @Override
  public int hashCode() {
    return Arrays.hashCode(this.w);
  }

  @Override
  public boolean equals(Object othat) {
    if (othat instanceof Hash256) {
      Hash256 that = (Hash256)othat;
      for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
        if (this.w[i] != that.w[i]) {
          return false;
        }
      }
      return true;
    } else {
      return false;
    }
  }

  @Override
  public int compareTo(Hash256 that) {
    for (int i = 0; i < HASH256_NUM_SLOTS; i++) {
      if (this.w[i] < that.w[i]) {
        return -1;
      } else if (this.w[i] > that.w[i]) {
        return 1;
      }
    }
    return 0;
  }

};
