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

#include <stdint.h>
#include <type_traits>
#include <vector>
namespace facebook {
namespace pdq {
namespace index {

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
        tmp[needlei] = ((uint64_t*)(&needles[needlei].w))[regi];
      }
      _packedNeedles[regi] = _mm512_xor_epi64(ones, _mm512_load_si512(tmp));
    }
  }
#else
  Flat(const std::array<facebook::pdq::hashing::Hash256, 8>& needles)
      : _needles(needles) {}
#endif

  ~Flat() {}

 private:
  // Disallow copying
  Flat(const Flat& /*that*/) {}
  void operator=(const facebook::pdq::hashing::Hash256& /*that*/) {}

 public:
#ifdef __AVX512VPOPCNTDQ__
  /**
   * @brief Test if any needles matched the index (haystack) in constant time
   *
   * @param haystack  array of 256-bit hashes
   * @param haystack_size  number of 256-bit hashes in the haystack
   * @param threshold  hamming distance threshold
   * @return true if the haystack matches the needles, false otherwise
   */
  bool test(
      const facebook::pdq::hashing::Hash256* haystack,
      size_t haystack_size,
      int threshold) const {
    const auto addend = _mm512_set1_epi64(threshold);

    auto result = _mm512_setzero_si512();
    for (size_t i = 0; i < haystack_size; i++) {
      const auto quadWords = (uint64_t*)&haystack[i].w;
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

    const auto test = _mm512_set1_epi64(256);
    const auto test_mask = _mm512_test_epi64_mask(result, test);

    return test_mask != 0;
  }
#else
  /**
   * @brief Test if the any needles matched the haystack in constant time
   *
   * @param haystack  array of 256-bit hashes
   * @param haystack_size  number of 256-bit hashes in the haystack
   * @param threshold  hamming distance threshold
   * @return true if the haystack matches the needles, false otherwise
   */
  bool test(
      const facebook::pdq::hashing::Hash256* haystack,
      size_t haystack_size,
      int threshold) const {
    bool matched = false;
    for (size_t i = 0; i < haystack_size; i++) {
      for (size_t j = 0; j < 8; j++) {
        matched |= (haystack[i].hammingDistance(_needles[j]) <= threshold);
      }
    }
    return matched;
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
      const auto quadWords = (uint64_t*)&haystack[i].w;
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
