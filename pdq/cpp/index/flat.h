// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef FLAT_H
#define FLAT_H

#include <array>
#include <pdq/cpp/common/pdqhashtypes.h>

#ifdef __AVX512VPOPCNTDQ__
#include <immintrin.h>
#endif

#include <cstdint>
#include <type_traits>
#include <vector>
namespace facebook {
namespace pdq {
namespace index {

// base assumptions using throughout the index for efficient data loading
static_assert(
    sizeof(facebook::pdq::hashing::Hash256) == 32,
    "Hash256 should be exactly 32 bytes");
static_assert(
    alignof(facebook::pdq::hashing::Hash256) == 8,
    "Hash256 should be 8 bytes aligned");

/**
 * @brief Flat index for PDQ matching based on amortized linear scan.
 *
 * The implementation is similar to FAISS IndexBinaryFlat but with PDQ-specific
 * memory layout optimizations, see issue #1810 for more details.
 *
 * No index building is required using this index, it simply needs a packed
 * array of the database hashes fed through the matching function.
 *
 * Metadata can be tracked using parallel arrays.
 *
 * Live mutations can be done by partitioning the database into multiple
 * subsets, then use atomic variables and other synchronization primitives to
 * ensure thread-safety.
 *
 * This index is intended for use when:
 *   - The query can be batched by 8 hashes at a time (the most common reason
 *     is to search all 8 dihedral variants of an image), AND
 *   - One of the following is true:
 *     - Minimal memory usage is desired, OR
 *     - The threshold varies widely (for example per-user risk-based
 * thresholds) at runtime making MIH too inflexible / space-inefficient, OR
 *     - Timing correlation between the content of the index and the query is
 *       unacceptable (use test() instead), OR
 *     - The runtime environment has a modern (2020+) AVX512 CPU with
 *       AVX512VPOPCNTDQ support, which can significantly outperform 8 MIH
 *       queries with much less pressure on microarchitectural resources,
 *       testing shows ~3x~6x improvement with an index of 10 million hashes
 *       depending on whether matches are found.
 */
class Flat {
#ifdef __AVX512VPOPCNTDQ__
  __m512i _packedNeedles[4];
#else
  std::array<facebook::pdq::hashing::Hash256, 8> _needles;
#endif

 public:
#ifdef __AVX512VPOPCNTDQ__
  static const bool SIMD_ACCELERATED = true;
#else
  static const bool SIMD_ACCELERATED = false;
#endif

#ifdef __AVX512VPOPCNTDQ__
  Flat(const std::array<facebook::pdq::hashing::Hash256, 8>& needles) {
    alignas(64) uint64_t tmp[8];

    const __m512i ones = _mm512_set1_epi64(~0ULL);

    // Split 256-bit hash into 4x64-bit words, then place each hash vertically
    // in 64-bit lanes. Finally complement all registers.

    for (size_t regi = 0; regi < 4; regi++) {
      for (size_t needlei = 0; needlei < 8; needlei++) {
        tmp[needlei] =
            reinterpret_cast<const uint64_t*>(needles[needlei].w)[regi];
      }
      _packedNeedles[regi] = _mm512_xor_epi64(ones, _mm512_load_si512(tmp));
    }
  }
#else
  Flat(const std::array<facebook::pdq::hashing::Hash256, 8>& needles)
      : _needles(needles) {}
#endif

  // Disallow copying
  Flat(const Flat&) = delete;
  Flat& operator=(const Flat&) = delete;
  Flat(Flat&&) = delete;
  Flat& operator=(Flat&&) = delete;
  ~Flat() = default;

 public:
#ifdef __AVX512VPOPCNTDQ__
  /**
   * @brief Test if any needles matched the index (haystack) in constant time
   * w.r.t. the contents of the index or query,
   * this is harder to use but more suitable for real-time screening with high
   * security requirements, and potentially slightly faster for the no-match
   * case.
   *
   * @param haystack  array of 256-bit hashes
   * @param haystack_size  number of 256-bit hashes in the haystack
   * @param threshold  hamming distance threshold
   * @return uint8_t a bitmask of which queries matched the haystack
   */
  uint8_t test(
      const facebook::pdq::hashing::Hash256* haystack,
      size_t haystack_size,
      int threshold) const {
    const auto addend = _mm512_set1_epi64(threshold);

    auto result = _mm512_setzero_si512();
    for (size_t i = 0; i < haystack_size; i++) {
      const auto quadWords = reinterpret_cast<const uint64_t*>(haystack[i].w);
      // broadcast each quad word to a register.
      const auto query0 = _mm512_set1_epi64(quadWords[0]);
      const auto query1 = _mm512_set1_epi64(quadWords[1]);
      const auto query2 = _mm512_set1_epi64(quadWords[2]);
      const auto query3 = _mm512_set1_epi64(quadWords[3]);

      // xor the query with the needles.
      const auto diff0 = _mm512_xor_epi64(query0, _packedNeedles[0]);
      const auto diff1 = _mm512_xor_epi64(query1, _packedNeedles[1]);
      const auto diff2 = _mm512_xor_epi64(query2, _packedNeedles[2]);
      const auto diff3 = _mm512_xor_epi64(query3, _packedNeedles[3]);

      // population count, since we complemented the query now the result is the
      // # of bits that were the same.
      const auto popcnt0 = _mm512_popcnt_epi64(diff0);
      const auto popcnt1 = _mm512_popcnt_epi64(diff1);
      const auto popcnt2 = _mm512_popcnt_epi64(diff2);
      const auto popcnt3 = _mm512_popcnt_epi64(diff3);

      // vertical summation
      const auto reduction0 = _mm512_add_epi64(popcnt0, popcnt1);
      const auto reduction1 = _mm512_add_epi64(popcnt2, popcnt3);
      const auto reduction = _mm512_add_epi64(reduction0, reduction1);

      // add the threshold, now if the distance was within threshold, this
      // distance would be between 256 and 256 * 2 - 1 (i.e. dist & 256 != 0)
      result = _mm512_or_si512(result, _mm512_add_epi64(reduction, addend));
    }

    const auto test = _mm512_set1_epi64(~255); // ignore the lower bits
    const auto test_mask = _mm512_test_epi64_mask(result, test);

    return test_mask;
  }
#else
  /**
   * @brief Test if the any needles matched the haystack in near-constant time,
   * minus microarchitectural variations that are more pronounced using scalar
   * code.
   *
   * @param haystack  array of 256-bit hashes
   * @param haystack_size  number of 256-bit hashes in the haystack
   * @param threshold  hamming distance threshold
   * @return uint8_t a bitmask of which queries matched the haystack
   */
  uint8_t test(
      const facebook::pdq::hashing::Hash256* haystack,
      size_t haystack_size,
      int threshold) const {
    uint8_t result = 0;
    for (size_t i = 0; i < haystack_size; i++) {
      for (size_t j = 0; j < 8; j++) {
        const auto matched =
            haystack[i].hammingDistance(_needles[j]) <= threshold;
        result |= ((uint8_t)matched << j);
      }
    }
    return result;
  }
#endif

#ifdef __AVX512VPOPCNTDQ__
  /**
   * @brief Query all matches in the haystack
   *
   * @param haystack  array of 256-bit hashes
   * @param haystack_size  number of 256-bit hashes in the haystack
   * @param threshold  hamming distance threshold
   * @param matches  vector of matches , in pairs of (haystack_index,
   * needle_index)
   */
  void queryAll(
      const facebook::pdq::hashing::Hash256* haystack,
      size_t haystack_size,
      int threshold,
      std::vector<std::pair<size_t, size_t>>& matches) const {
    const auto threshold_v = _mm512_set1_epi64(256 - threshold);

    for (size_t i = 0; i < haystack_size; i++) {
      // broadcast each quad word to a register.
      const auto quadWords = reinterpret_cast<const uint64_t*>(haystack[i].w);
      const auto query0 = _mm512_set1_epi64(quadWords[0]);
      const auto query1 = _mm512_set1_epi64(quadWords[1]);
      const auto query2 = _mm512_set1_epi64(quadWords[2]);
      const auto query3 = _mm512_set1_epi64(quadWords[3]);

      // xor the query with the needles.
      const auto diff0 = _mm512_xor_epi64(query0, _packedNeedles[0]);
      const auto diff1 = _mm512_xor_epi64(query1, _packedNeedles[1]);
      const auto diff2 = _mm512_xor_epi64(query2, _packedNeedles[2]);
      const auto diff3 = _mm512_xor_epi64(query3, _packedNeedles[3]);

      // population count, since we complemented the query now the result is the
      // # of bits that were the same.
      const auto popcnt0 = _mm512_popcnt_epi64(diff0);
      const auto popcnt1 = _mm512_popcnt_epi64(diff1);
      const auto popcnt2 = _mm512_popcnt_epi64(diff2);
      const auto popcnt3 = _mm512_popcnt_epi64(diff3);

      // vertical summation
      const auto reduction0 = _mm512_add_epi64(popcnt0, popcnt1);
      const auto reduction1 = _mm512_add_epi64(popcnt2, popcnt3);
      const auto reduction = _mm512_add_epi64(reduction0, reduction1);

      // compare the reduction with the threshold
      // test if any has value >= (256 - threshold)
      auto test = _mm512_cmpge_epi64_mask(reduction, threshold_v);

      // pop off any set bit in the mask
      while (
#if defined(__GNUC__)
          __builtin_expect(test != 0, 0)
#else
          test != 0
#endif
      )
#if defined(__cplusplus) && __cplusplus >= 202002L
        [[unlikely]]
#endif
        {
          const auto index = _tzcnt_u64(test);
          matches.emplace_back(i, index);
          test ^= 1ULL << index;
        }
    }
  }
#else
  void queryAll(
      const facebook::pdq::hashing::Hash256* haystack,
      size_t haystack_size,
      int threshold,
      std::vector<std::pair<size_t, size_t>>& matches) const {
    for (size_t i = 0; i < haystack_size; i++) {
      for (size_t j = 0; j < 8; j++) {
        if (haystack[i].hammingDistance(_needles[j]) <= threshold) {
          matches.emplace_back(i, j);
        }
      }
    }
  }
#endif
};

} // namespace index
} // namespace pdq
} // namespace facebook

#endif // FLAT_H
