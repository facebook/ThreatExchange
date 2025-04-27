// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef PDQHAMMING_H
#define PDQHAMMING_H

#include <bitset>

#include <pdq/cpp/common/pdqbasetypes.h>

// USE_BUILTIN_POPCOUNT controls how the popcount is calculated.
// If it is not defined, the popcount will be calculated with lookup tables.
// If it is defined, it calculates popcount using bitset. This generally is
// generally faster because it compile directly to popcount instruction on some
// architectures, e.g., x86-64 and aarch64.
#define USE_BUILTIN_POPCOUNT

namespace facebook {
namespace pdq {
namespace hashing {

#ifdef USE_BUILTIN_POPCOUNT

/**
 * @brief Returns the number of bits set.
 *
 * @param T An unsigned integer type.
 */
template <typename T>
int popcount(T const x) {
  return static_cast<int>(std::bitset<sizeof(T) * 8U>(x).count());
}

/**
 * @brief Returns the number of different bits between two numbers.
 *
 * @param T An unsigned integer type.
 */
template <typename T>
int hammingDistance(const T a, const T b) {
  return popcount(a ^ b);
}

inline int hammingNorm8(Hash8 h) {
  return popcount<Hash8>(h);
}
inline int hammingNorm16(Hash16 h) {
  return popcount<Hash16>(h);
}
inline int hammingDistance8(Hash8 a, Hash8 b) {
  return hammingDistance<Hash8>(a, b);
}
inline int hammingDistance16(Hash16 a, Hash16 b) {
  return hammingDistance<Hash16>(a, b);
}
inline int hammingDistance64(Hash64 a, Hash64 b) {
  return hammingDistance<Hash64>(a, b);
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
