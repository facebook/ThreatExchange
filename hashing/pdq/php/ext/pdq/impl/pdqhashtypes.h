// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#ifndef PDQHASHTYPES_H
#define PDQHASHTYPES_H

// ================================================================
// 256-bit hashes with Hamming distance
// ================================================================

#include <stdio.h>
#include "pdqbasetypes.h"

// ----------------------------------------------------------------
// 16-bit words are essential for the MIH data structure.
#define HASH256_NUM_WORDS   16
#define HASH256_TEXT_LENGTH 65

// Hex-formatted strings.
typedef char Hash256Text[HASH256_TEXT_LENGTH];

// ================================================================
// We could use 32 bytes, 16 16-bit ints, 8 32-bit ints, or 4 64-bit ints.
// For mutually indexed hashing in the C++ implementation, 16x16 is best
// so that's what we use here as well.

typedef struct _Hash256 {
  Hash16 w[HASH256_NUM_WORDS];
} Hash256;

void Hash256Clear(Hash256* phash);
void Hash256SetBit(Hash256* phash, int k);

// Buffer should have length HASH256_TEXT_LENGTH.
// Returns buffer.
char* Hash256Format(Hash256* phash, char* buffer);

#endif // PDQHASHTYPES_H
