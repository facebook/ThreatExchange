// Copyright (c) Meta Platforms, Inc. and affiliates.
#include "pdqhashtypes.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>


// ----------------------------------------------------------------
void Hash256Clear(Hash256* phash) {
  for (int i = 0; i < HASH256_NUM_WORDS; i++) {
    phash->w[i] = 0;
  }
}

// ----------------------------------------------------------------
void Hash256SetBit(Hash256* phash, int k) {
	phash->w[(k & 255) >> 4] ^= 1 << (k & 15);
}

static const char hash256_format[] =
  "%04hx%04hx%04hx%04hx%04hx%04hx%04hx%04hx"
  "%04hx%04hx%04hx%04hx%04hx%04hx%04hx%04hx";

// ----------------------------------------------------------------
// Buffer should have length HASH256_TEXT_LENGTH
char* Hash256Format(Hash256* phash, char* buffer) {
  snprintf(buffer, HASH256_TEXT_LENGTH, hash256_format,
    phash->w[15], phash->w[14], phash->w[13], phash->w[12],
    phash->w[11], phash->w[10], phash->w[9],  phash->w[8],
    phash->w[7],  phash->w[6],  phash->w[5],  phash->w[4],
    phash->w[3],  phash->w[2],  phash->w[1],  phash->w[0]
  );
  return buffer;
}
