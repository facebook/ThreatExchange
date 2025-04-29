// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <vector>
#include <pdq/cpp/common/pdqbasetypes.h>
#include <pdq/cpp/common/pdqutils.h>
#include <pdq/cpp/index/flat.h>

void expectTest(
    const std::vector<facebook::pdq::hashing::Hash256>& haystack,
    const std::array<facebook::pdq::hashing::Hash256, 8>& needles,
    const size_t maxDistance,
    const uint8_t expected) {
  facebook::pdq::index::Flat flat(needles);
  const auto result = flat.test(haystack.data(), haystack.size(), maxDistance);
  if (result != expected) {
    fprintf(stderr, "test failed: expected %d, got %d\n", expected, result);
    exit(1);
  }
}

// ----------------------------------------------------------------
// test that under misuse and nonsensical input the function still yield
// numerically correct results
void test_misuse(
    std::vector<facebook::pdq::hashing::Hash256>& haystack,
    const std::array<facebook::pdq::hashing::Hash256, 8>& needles) {
  const facebook::pdq::hashing::Hash256 backup(haystack[0]);
  const auto needles_comp = ~needles[0];
  haystack[0] = needles_comp;
  expectTest(haystack, needles, 0, 0);
  expectTest(haystack, needles, 31, 0);
  expectTest(haystack, needles, 64, 0);
  expectTest(haystack, needles, 256, ~0);
  expectTest(haystack, needles, 999, ~0);
}

// ----------------------------------------------------------------
// test that 1 hit can appear at any cartesian product of needle and haystack,
// with 0 or maxDistance fuzzed
void test_1hit(
    std::vector<facebook::pdq::hashing::Hash256>& haystack,
    const std::array<facebook::pdq::hashing::Hash256, 8>& needles,
    const size_t maxDistance) {
  const size_t HAYSTACK_SIZE = haystack.size();
  std::vector<std::pair<size_t, size_t>> matches;

  for (size_t fuzz : std::array<size_t, 2>{0, maxDistance}) {
    for (size_t i = 0; i < HAYSTACK_SIZE; i++) {
      for (size_t j = 0; j < 8; j++) {
        const auto backup = haystack[i];
        haystack[i] = facebook::pdq::hashing::Hash256(needles[j]).fuzz(fuzz);
        expectTest(haystack, needles, maxDistance, 1 << j);

        facebook::pdq::index::Flat flat(needles);
        flat.queryAll(haystack.data(), haystack.size(), maxDistance, matches);
        if (matches.size() != 1) {
          fprintf(
              stderr, "test failed: expected 1 hit, got %zu\n", matches.size());
          exit(1);
        } else if (matches[0] != std::make_pair(i, j)) {
          fprintf(
              stderr,
              "test failed: expected hit at (%zu, %zu), got (%zu, %zu)\n",
              i,
              j,
              matches[0].first,
              matches[0].second);
          exit(1);
        }
        matches.clear();

        haystack[i] = backup;
      }
    }
  }
}

// ----------------------------------------------------------------
// test that 2 hits can appear at any cartesian product of needle and haystack,
// with 0 or maxDistance fuzzed
void test_2hits(
    std::vector<facebook::pdq::hashing::Hash256>& haystack,
    const std::array<facebook::pdq::hashing::Hash256, 8>& needles,
    const size_t maxDistance) {
  const size_t HAYSTACK_SIZE = haystack.size();
  std::vector<std::pair<size_t, size_t>> matches;

  for (size_t fuzz : std::array<size_t, 2>{0, maxDistance}) {
    for (size_t i = 0; i < HAYSTACK_SIZE - 1; i++) {
      for (size_t j0 = 0; j0 < 8; j0++) {
        for (size_t j1 = j0 + 1; j1 < 8; j1++) {
          const auto backup0 = haystack[i];
          const auto backup1 = haystack[i + 1];
          haystack[i] = facebook::pdq::hashing::Hash256(needles[j0]).fuzz(fuzz);
          haystack[i + 1] =
              facebook::pdq::hashing::Hash256(needles[j1]).fuzz(fuzz);
          expectTest(haystack, needles, maxDistance, (1 << j0) | (1 << j1));

          facebook::pdq::index::Flat flat(needles);
          flat.queryAll(haystack.data(), haystack.size(), maxDistance, matches);
          if (matches.size() != 2) {
            fprintf(
                stderr,
                "test failed: expected 2 hits, got %zu\n",
                matches.size());
            exit(1);
          } else if (
              matches[0] != std::make_pair(i, j0) ||
              matches[1] != std::make_pair(i + 1, j1)) {
            fprintf(
                stderr,
                "test failed: expected hits at (%zu, %zu) and (%zu, %zu), got (%zu, %zu) and (%zu, %zu)\n",
                i,
                j0,
                i + 1,
                j1,
                matches[0].first,
                matches[0].second,
                matches[1].first,
                matches[1].second);
            exit(1);
          }
          matches.clear();

          haystack[i] = backup0;
          haystack[i + 1] = backup1;
        }
      }
    }
  }
}

// ----------------------------------------------------------------
// test that any hash can appear with 1 extra bit flipped and it should not
// appear in matches
void test_false_positive(
    std::mt19937& gen,
    std::vector<facebook::pdq::hashing::Hash256>& haystack,
    const std::array<facebook::pdq::hashing::Hash256, 8>& needles,
    const size_t maxDistance) {
  const size_t HAYSTACK_SIZE = haystack.size();
  std::vector<std::pair<size_t, size_t>> matches;

  for (size_t i = 0; i < HAYSTACK_SIZE; i++) {
    for (size_t j = 0; j < 8; j++) {
      facebook::pdq::hashing::Hash256 mutated(needles[j]);

      while (true) {
        // flip just one more than needed to match
        const auto bitsToFlip =
            maxDistance + 1 - mutated.hammingDistance(needles[j]);
        if (bitsToFlip == 0) {
          break;
        }
        mutated = facebook::pdq::hashing::addNoise(mutated, bitsToFlip, gen);
      }

      const facebook::pdq::hashing::Hash256 backup(haystack[i]);
      haystack[i] = mutated;
      expectTest(haystack, needles, maxDistance, 0);

      facebook::pdq::index::Flat flat(needles);
      flat.queryAll(haystack.data(), haystack.size(), maxDistance, matches);
      if (matches.size() != 0) {
        fprintf(
            stderr, "test failed: expected 0 hits, got %zu\n", matches.size());
        exit(1);
      }
      matches.clear();

      haystack[i] = backup;
    }
  }
}

int main(int argc, char** argv) {
  const size_t HAYSTACK_SIZE =
      facebook::pdq::index::Flat::SIMD_ACCELERATED ? 1000 : 200;

  if (facebook::pdq::index::Flat::SIMD_ACCELERATED) {
    printf("Using SIMD accelerated flat index\n");
  } else {
    printf("Using scalar flat index\n");
  }

  std::mt19937 gen(41);

  std::vector<facebook::pdq::hashing::Hash256> haystack;

  for (size_t i = 0; i < HAYSTACK_SIZE; i++) {
    haystack.push_back(facebook::pdq::hashing::generateRandomHash(gen));
  }

  std::array<facebook::pdq::hashing::Hash256, 8> needles;
  for (int i = 0; i < 8; i++) {
    needles[i] = facebook::pdq::hashing::generateRandomHash(gen);
  }

  for (size_t maxDistance : std::array<size_t, 3>{0, 31, 64}) {
    printf("Testing maxDistance = %zu\n", maxDistance);

    // make sure no hits at the beginning
    expectTest(haystack, needles, maxDistance, 0);
    printf("\tPASS: initially no hits\n");

    test_1hit(haystack, needles, maxDistance);
    printf("\tPASS: 1 hit\n");

    test_2hits(haystack, needles, maxDistance);
    printf("\tPASS: 2 hits\n");

    test_false_positive(gen, haystack, needles, maxDistance);
    printf("\tPASS: no edge-case false positives\n");

    // make sure no hits at the end
    expectTest(haystack, needles, maxDistance, 0);
    printf("\tPASS: no hits at the end\n");
  }

  printf("Testing correctness under misuse\n");
  test_misuse(haystack, needles);
  printf("\tPASS: correctness under misuse\n");

  return 0;
}