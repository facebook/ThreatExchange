// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#include <pdq/cpp/common/pdqhashtypes.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <stdexcept>

namespace facebook {
namespace pdq {
namespace hashing {

const char hash256_format[] =
    "%04hx%04hx%04hx%04hx%04hx%04hx%04hx%04hx"
    "%04hx%04hx%04hx%04hx%04hx%04hx%04hx%04hx";

// ================================================================
Hash256::Hash256(const char* hex_formatted_string) {
  if (strlen(hex_formatted_string) != 64) {
    throw std::runtime_error(
        "pdqhash: malformed \"" + std::string(hex_formatted_string) + "\"");
  }
  int rv = sscanf(
      hex_formatted_string,
      hash256_format,
      &this->w[15],
      &this->w[14],
      &this->w[13],
      &this->w[12],
      &this->w[11],
      &this->w[10],
      &this->w[9],
      &this->w[8],
      &this->w[7],
      &this->w[6],
      &this->w[5],
      &this->w[4],
      &this->w[3],
      &this->w[2],
      &this->w[1],
      &this->w[0]);
  if (rv != 16) {
    throw std::runtime_error(
        "pdqhash: malformed \"" + std::string(hex_formatted_string) + "\"");
  }
}

// ----------------------------------------------------------------
Hash256 Hash256::fromLineOrDie(char* line, int linelen) {
  if (line[linelen - 1] == '\n') {
    line[linelen - 1] = 0;
  }
  return Hash256::fromStringOrDie(line);
}

// ----------------------------------------------------------------
Hash256 Hash256::fromStringOrDie(char* string) {
  Hash256 h;
  if (strlen(string) != 64) {
    // could throw; only current use is ops-tools which
    // would exit anyway.
    fprintf(stderr, "Scan \"%s\" failed.\n", string);
    exit(1);
  }
  int rv = sscanf(
      string,
      hash256_format,
      &h.w[15],
      &h.w[14],
      &h.w[13],
      &h.w[12],
      &h.w[11],
      &h.w[10],
      &h.w[9],
      &h.w[8],
      &h.w[7],
      &h.w[6],
      &h.w[5],
      &h.w[4],
      &h.w[3],
      &h.w[2],
      &h.w[1],
      &h.w[0]);
  if (rv != 16) {
    // could throw; only current use is ops-tools which
    // would exit anyway.
    fprintf(stderr, "Scan \"%s\" failed.\n", string);
    exit(1);
  }
  return h;
}

// ----------------------------------------------------------------
std::string Hash256::format() const {
  Hash256Text buffer;
  snprintf(
      buffer,
      HASH256_TEXT_LENGTH,
      hash256_format,
      this->w[15],
      this->w[14],
      this->w[13],
      this->w[12],
      this->w[11],
      this->w[10],
      this->w[9],
      this->w[8],
      this->w[7],
      this->w[6],
      this->w[5],
      this->w[4],
      this->w[3],
      this->w[2],
      this->w[1],
      this->w[0]);
  std::string rv(buffer);
  return rv;
}

// ----------------------------------------------------------------
bool Hash256::operator<(const Hash256& that) const {
  Hash256 rv;
  for (int i = 0; i < HASH256_NUM_WORDS; i++) {
    int d = (int)this->w[i] - (int)that.w[i];
    if (d < 0) {
      return true;
    } else if (d > 0) {
      return false;
    }
  }
  return false;
}

bool Hash256::operator<=(const Hash256& that) const {
  Hash256 rv;
  for (int i = 0; i < HASH256_NUM_WORDS; i++) {
    int d = (int)this->w[i] - (int)that.w[i];
    if (d < 0) {
      return true;
    } else if (d > 0) {
      return false;
    }
  }
  return true;
}

bool Hash256::operator>(const Hash256& that) const {
  Hash256 rv;
  for (int i = 0; i < HASH256_NUM_WORDS; i++) {
    int d = (int)this->w[i] - (int)that.w[i];
    if (d > 0) {
      return true;
    } else if (d < 0) {
      return false;
    }
  }
  return false;
}

bool Hash256::operator>=(const Hash256& that) const {
  Hash256 rv;
  for (int i = 0; i < HASH256_NUM_WORDS; i++) {
    int d = (int)this->w[i] - (int)that.w[i];
    if (d > 0) {
      return true;
    } else if (d < 0) {
      return false;
    }
  }
  return true;
}

bool Hash256::operator==(const Hash256& that) const {
  Hash256 rv;
  for (int i = 0; i < HASH256_NUM_WORDS; i++) {
    if (this->w[i] != (int)that.w[i]) {
      return false;
    }
  }
  return true;
}

// ----------------------------------------------------------------
// Does not itself call srandom(); caller must.
Hash256 Hash256::fuzz(int numErrorBits) {
  Hash256 rv = *this;
  for (int i = 0; i < numErrorBits; i++) {
    int idx = random() % 256;
    rv.flipBit(idx);
  }
  return rv;
}

} // namespace hashing
} // namespace pdq
} // namespace facebook
