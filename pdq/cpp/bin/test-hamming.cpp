// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#include <pdq/cpp/common/pdqbasetypes.h>
#include <pdq/cpp/common/pdqhamming.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ================================================================
// Tests optimized Hamming-distance functions against their naive counterparts.
//
// For regression-test usage.
// ================================================================

using namespace facebook::pdq::hashing;

static bool test_8_uncached_against_slow_or_die();
static bool test_8_cached_against_slow_or_die();
static bool test_16_uncached_against_slow_or_die();
static bool test_16_cached_against_slow_or_die();

int main(int argc, char** argv) {
  bool ok = true;

  printf("================================================================\n");
  ok &= test_8_uncached_against_slow_or_die();
  ok &= test_8_cached_against_slow_or_die();
  ok &= test_16_uncached_against_slow_or_die();
  ok &= test_16_cached_against_slow_or_die();
  printf("================================================================\n");

  return ok ? 0 : 1;
}

// ----------------------------------------------------------------
static bool test_8_uncached_against_slow_or_die() {
  bool ok = true;
  for (int i = 0; i < 256; i++) {
    Hash8 a = i;
    int uncached = hammingNorm8Uncached(a);
    int slow = hammingNorm8Slow(a);
    if (uncached != slow) {
      fprintf(stderr, "8-bit hamming uncached(%02xx) = %d != slow %d\n",
        (unsigned)a,
        uncached,
        slow
      );
    }
  }
  printf("hamming test_8_uncached_against_slow_or_die %s\n",
    ok ? "PASS" : "FAIL");
  return ok;
}

// ----------------------------------------------------------------
static bool test_8_cached_against_slow_or_die() {
  bool ok = true;
  for (int i = 0; i < 256; i++) {
    Hash8 a = i;
    int cached = hammingNorm8(a);
    int slow = hammingNorm8Slow(a);
    if (cached != slow) {
      fprintf(stderr, "8-bit hamming cached(%02xx) = %d != slow %d\n",
        (unsigned)a,
        cached,
        slow
      );
    }
  }
  printf("hamming test_8_cached_against_slow_or_die %s\n",
    ok ? "PASS" : "FAIL");
  return ok;
}

// ----------------------------------------------------------------
static bool test_16_uncached_against_slow_or_die() {
  bool ok = true;
  for (int i = 0; i < 65536; i++) {
    Hash16 a = i;
    int uncached = hammingNorm16Uncached(a);
    int slow = hammingNorm16Slow(a);
    if (uncached != slow) {
      fprintf(stderr, "16-bit hamming uncached(%02xx) = %d != slow %d\n",
        (unsigned)a,
        uncached,
        slow
      );
    }
  }
  printf("hamming test_16_uncached_against_slow_or_die %s\n",
    ok ? "PASS" : "FAIL");
  return ok;
}

// ----------------------------------------------------------------
static bool test_16_cached_against_slow_or_die() {
  bool ok = true;
  for (int i = 0; i < 65536; i++) {
    Hash16 a = i;
    int cached = hammingNorm16(a);
    int slow = hammingNorm16Slow(a);
    if (cached != slow) {
      fprintf(stderr, "16-bit hamming cached(%02xx) = %d != slow %d\n",
        (unsigned)a,
        cached,
        slow
      );
    }
  }
  printf("hamming test_16_cached_against_slow_or_die %s\n",
    ok ? "PASS" : "FAIL");
  return ok;
}
