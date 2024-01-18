// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef PDQHAMMING_H
#define PDQHAMMING_H

#include <bitset>

#include <pdq/cpp/common/pdqbasetypes.h>

// OLD NOTICE:
// If your compiler doesn't support __builtin_popcount then feel free to
// undefine this. (Experiments have shown that using builtin popcount helps
// performance by a few percent -- worth using but OK to live without.)
//
// NOTICE:
// __builin_popcount was replaced by std::bitset<>::count()
// The define is left here for backwards compatibility
// if you want to use the lookup table.
#define USE_BUILTIN_POPCOUNT

namespace facebook {
namespace pdq {
namespace hashing {

#ifdef USE_BUILTIN_POPCOUNT
// Inlined right here
inline int hammingNorm8(Hash8 h) {
  return std::bitset<8>(h).count();
}
inline int hammingNorm16(Hash16 h) {
  return std::bitset<16>(h).count();
}
inline int hammingDistance8(Hash8 a, Hash8 b) {
  return std::bitset<8>(a ^ b).count();
}
inline int hammingDistance16(Hash16 a, Hash16 b) {
  return std::bitset<16>(a ^ b).count();
}
#else
// Implemented in pdqhamming.cpp with lookup tables.
int hammingNorm8(Hash8 h);
int hammingNorm16(Hash16 h);
int hammingDistance8(Hash8 a, Hash8 b);
int hammingDistance16(Hash16 a, Hash16 b);
#endif

// For regression/portability testing
int hammingNorm8Uncached(Hash8 h);
int hammingNorm16Uncached(Hash16 h);
int hammingNorm8Slow(Hash8 a);
int hammingNorm16Slow(Hash16 a);

} // namespace hashing
} // namespace pdq
} // namespace facebook

#endif // PDQHAMMING_H
