// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#ifndef PDQHAMMING_H
#define PDQHAMMING_H

#include <pdq/cpp/common/pdqbasetypes.h>

// If your compiler doesn't support __builtin_popcount then feel free to
// undefine this. (Experiments have shown that using builtin popcount helps
// performance by a few percent -- worth using but OK to live without.)
#define USE_BUILTIN_POPCOUNT

namespace facebook {
namespace pdq {
namespace hashing {

#ifdef USE_BUILTIN_POPCOUNT
// Inlined right here
inline int hammingNorm8(Hash8 h) {
  return __builtin_popcount((unsigned)h);
}
inline int hammingNorm16(Hash16 h) {
  return __builtin_popcount((unsigned)h);
}
inline int hammingDistance8(Hash8 a, Hash8 b) {
  return __builtin_popcount((unsigned)(a^b));
}
inline int hammingDistance16(Hash16 a, Hash16 b) {
  return __builtin_popcount((unsigned)(a^b));
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
