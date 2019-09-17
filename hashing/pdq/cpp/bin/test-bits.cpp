// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#include <pdq/cpp/common/pdqhashtypes.h>
#include <pdq/cpp/common/pdqhamming.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ================================================================
// Tests bit-flips. Output is to stdout and regressed using reg_test/run.
// ================================================================

using namespace facebook::pdq::hashing;

int main(int argc, char** argv) {
  bool ok = true;

  printf("================================================================\n");
  Hash256 hash;

  printf("%s\n", hash.format().c_str());

  printf("\n");
  for (int i = 0; i < 256; i++) {
    hash.setBit(i);
    printf("%s set %d\n", hash.format().c_str(), i);
  }

  printf("\n");
  for (int i = 0; i < 256; i++) {
    hash.clearBit(i);
    printf("%s clear %d\n", hash.format().c_str(), i);
  }

  printf("\n");
  for (int i = 0; i < 256; i++) {
    hash.flipBit(i);
    printf("%s flip %d\n", hash.format().c_str(), i);
  }

  hash.clear();
  for (int i = 0; i < 16; i++) {
    hash.setBit(i*i);
  }
  printf("\n");
  printf("%s\n", hash.format().c_str());

  for (int i = 0; i < 256; i++) {
    printf("%3d %d\n", i, hash.getBit(i));
  }

  printf("================================================================\n");

  return ok ? 0 : 1;
}
