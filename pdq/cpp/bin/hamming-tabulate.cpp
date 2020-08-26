// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#include <pdq/cpp/common/pdqbasetypes.h>
#include <pdq/cpp/common/pdqhamming.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

using namespace facebook::pdq::hashing;

// ----------------------------------------------------------------
// Computes lookup tables for 8-bit Hamming distances.  You can invoke this
// manually and put the result into pdqhamming.cpp.  This is intended to be
// invoked precisely once, for precomputing the hamming-distance tables.

int main(int argc, char** argv) {

  printf("static Hash8 hash8_norm_lookup_table[] = {\n");
  for (int i = 0; i < 256; i++) {
    Hash8 h = i;
    int n = hammingNorm8Uncached(h);

    if ((i % 4) == 0) {
      printf(" ");
    }
    printf("%2d/*%02x*/", n, i);
    if (i < 255) {
      printf(",");
    }
    if ((i % 4) != 3) {
      printf(" ");
    } else {
      printf("\n");
    }
  }
  printf("};\n");

  printf("static Hash16 hash16_norm_lookup_table[] = {\n");
  for (int i = 0; i < 65536; i++) {
    Hash16 h = i;
    int n = hammingNorm16Uncached(h);

    if ((i % 4) == 0) {
      printf(" ");
    }
    printf("%2d/*%02x*/", n, i);
    if (i < 65535) {
      printf(",");
    }
    if ((i % 4) != 3) {
      printf(" ");
    } else {
      printf("\n");
    }
  }
  printf("};\n");

  return 0;
}
