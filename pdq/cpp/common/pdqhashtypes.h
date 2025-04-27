// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef PDQHASHTYPES_H
#define PDQHASHTYPES_H

// ================================================================
// 256-bit hashes with Hamming distance
// ================================================================

#include <pdq/cpp/common/pdqbasetypes.h>
#include <pdq/cpp/common/pdqhamming.h>

#include <bitset>
#include <cinttypes>
#include <string>

namespace facebook {
namespace pdq {
namespace hashing {

// ----------------------------------------------------------------
// 16-bit words are essential for the MIH data structure.
// Read more at https://fburl.com/pdq-hashing-mih
const int HASH256_NUM_BITS = 256;
const int HASH256_NUM_WORDS = 16;
const int HASH256_TEXT_LENGTH = 65;

// Hex-formatted strings.
using Hash256Text = char[HASH256_TEXT_LENGTH];

// ================================================================
struct Hash256 {
  // align to 64-bit boundary for faster scalar popcnt
  // (compiler can optimize without peeling to natural word size)
  // index/flat.h also relies on this assumption, do not remove.
  alignas(8) Hash16 w[HASH256_NUM_WORDS];

  int getNumWords() const { return HASH256_NUM_WORDS; }

  Hash256() {
    for (int i = 0; i < HASH256_NUM_WORDS; i++) {
      this->w[i] = 0;
    }
  }

  explicit Hash256(const char* hex_formatted_hash);

  Hash256(const Hash256& that) {
    for (int i = 0; i < HASH256_NUM_WORDS; i++) {
      this->w[i] = that.w[i];
    }
  }

  Hash256& operator=(const Hash256& that) {
    if (&that == this) {
      return *this;
    }
    for (int i = 0; i < HASH256_NUM_WORDS; i++) {
      this->w[i] = that.w[i];
    }
    return *this;
  }

  void clear() {
    for (int i = 0; i < HASH256_NUM_WORDS; i++) {
      this->w[i] = 0;
    }
  }

  void setAll() {
    for (int i = 0; i < HASH256_NUM_WORDS; i++) {
      this->w[i] = ~0;
    }
  }

  int hammingNorm() {
    int n = 0;
    for (int i = 0; i < HASH256_NUM_WORDS; i++) {
      n += hammingNorm16(this->w[i]);
    }
    return n;
  }

  int hammingDistance(const Hash256& that) const {
    const uint64_t* this_words = reinterpret_cast<const uint64_t*>(this->w);
    const uint64_t* that_words = reinterpret_cast<const uint64_t*>(that.w);
    return hammingDistance64(this_words[0], that_words[0]) +
        hammingDistance64(this_words[1], that_words[1]) +
        hammingDistance64(this_words[2], that_words[2]) +
        hammingDistance64(this_words[3], that_words[3]);
  }

  int getBit(int k) const { return (this->w[(k & 255) >> 4] >> (k & 15)) & 1; }

  void setBit(int k) { this->w[(k & 255) >> 4] |= 1 << (k & 15); }

  void clearBit(int k) { this->w[(k & 255) >> 4] &= ~(1 << (k & 15)); }

  void flipBit(int k) { this->w[(k & 255) >> 4] ^= 1 << (k & 15); }

  Hash256 operator^(const Hash256& that) const {
    Hash256 rv;
    for (int i = 0; i < HASH256_NUM_WORDS; i++) {
      rv.w[i] = this->w[i] ^ that.w[i];
    }
    return rv;
  }

  Hash256 operator&(const Hash256& that) const {
    Hash256 rv;
    for (int i = 0; i < HASH256_NUM_WORDS; i++) {
      rv.w[i] = this->w[i] & that.w[i];
    }
    return rv;
  }

  Hash256 operator|(const Hash256& that) const {
    Hash256 rv;
    for (int i = 0; i < HASH256_NUM_WORDS; i++) {
      rv.w[i] = this->w[i] | that.w[i];
    }
    return rv;
  }

  Hash256 operator~() const {
    Hash256 rv;
    for (int i = 0; i < HASH256_NUM_WORDS; i++) {
      rv.w[i] = ~this->w[i];
    }
    return rv;
  }

  // Needed for STL
  bool operator<(const Hash256& that) const;
  bool operator<=(const Hash256& that) const;
  bool operator>(const Hash256& that) const;
  bool operator>=(const Hash256& that) const;
  bool operator==(const Hash256& that) const;

  static Hash256 fromLineOrDie(std::string& line);
  static Hash256 fromStringOrDie(const std::string& string);

  std::string format() const;
  void dump() { printf("%s", this->format().c_str()); }

  // Flips some number of bits randomly, with replacement.  (I.e. not all
  // flipped bits are guaranteed to be in different positions; if you pass
  // argument of 10 then maybe 2 bits will be flipped and flipped back, and
  // only 6 flipped once.)
  Hash256 fuzz(int numErrorBits);

  void dumpBits() {
    for (int i = HASH256_NUM_WORDS - 1; i >= 0; i--) {
      Hash16 word = this->w[i];
      for (int j = 15; j >= 0; j--) {
        if (word & (1 << j)) {
          printf(" 1");
        } else {
          printf(" 0");
        }
      }
      printf("\n");
    }
    printf("\n");
  }

  void dumpWords() {
    for (int i = HASH256_NUM_WORDS - 1; i >= 0; i--) {
      Hash16 word = this->w[i];
      printf("%04hx", word);
      if (i > 0) {
        printf(" ");
      }
    }
    printf("\n");
  }
};

static_assert(sizeof(Hash256) == 32, "Hash256 should be 32 bytes");

int hammingDistance(const Hash256& hash1, const Hash256& hash2);
std::string hashToString(const Hash256& hash);

} // namespace hashing
} // namespace pdq
} // namespace facebook

#endif // PDQHASHTYPES_H
