// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.types;

import pdqhashing.types.Hash256;
import pdqhashing.types.PDQHashFormatException;
import java.io.PrintStream;
import java.util.Arrays;
import java.util.Random;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 256-bit hashes with Hamming distance
 */
public class HashInt64 {
  public static final int HASH_INT64_NUM_VALS = 4;

  // 4 slots of 64 bits each. See ../sql/README.md for why int64 values are
  // useful
  public final long[] w;

  // ----------------------------------------------------------------
  public HashInt64() {
    this.w = new long[HASH_INT64_NUM_VALS];
    for (int i = 0; i < HASH_INT64_NUM_VALS; i++) {
      this.w[i] = 0;
    }
  }

  // ----------------------------------------------------------------
  // Helper method to do sign extension
  private int toWord(short w) {
    return (int)w & 0xffff;
  }

  public HashInt64(Hash256 that) {
    this.w = new long[HASH_INT64_NUM_VALS];
    int j = 0;
    for (int i = Hash256.HASH256_NUM_SLOTS - 1; i >= 0;) {
      long val = toWord(that.w[i--]);
      val = (val << 16) ^ toWord(that.w[i--]);
      val = (val << 16) ^ toWord(that.w[i--]);
      val = (val << 16) ^ toWord(that.w[i--]);
      this.w[j++] = val;
    }
  }

  // ----------------------------------------------------------------
  public void dumpVals(PrintStream o) {
    for (int i = 0; i < HASH_INT64_NUM_VALS; i++) {
      o.printf("%d", this.w[i]);
      if (i < HASH_INT64_NUM_VALS-1)
        o.printf(" ");
    }
    o.printf("\n");
  }
};
