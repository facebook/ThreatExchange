// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <algorithm>
#include <chrono>
#include <iostream>
#include <random>
#include <string>
#include <vector>
#include <pdq/cpp/common/pdqutils.h>

Timer::Timer(const std::string& context, bool printOnEnter)
    : context_(context),
      printOnEnter_(printOnEnter),
      startTime_(std::chrono::steady_clock::now()) {
  if (printOnEnter_) {
    std::cout << context_ << "..." << std::endl;
  }
}

double Timer::elapsed() const {
  auto now = std::chrono::steady_clock::now();
  std::chrono::duration<double> elapsed = now - startTime_;
  return elapsed.count();
}

namespace facebook {
namespace pdq {
namespace hashing {

// Generate random hash
Hash256 generateRandomHash(std::mt19937& gen) {
  Hash256 hash;
  std::uniform_int_distribution<uint16_t> dist(0, UINT16_MAX);

  for (int i = 0; i < HASH256_NUM_WORDS; i++) {
    hash.w[i] = dist(gen);
  }
  return hash;
}

// Add noise to hash by flipping random bits
Hash256 addNoise(
    const Hash256& original, int numBitsToFlip, std::mt19937& gen) {
  Hash256 noisy = original;
  std::vector<int> bitIndices(256);
  for (int i = 0; i < 256; i++)
    bitIndices[i] = i;
  std::shuffle(bitIndices.begin(), bitIndices.end(), gen);
  for (int i = 0; i < numBitsToFlip; i++) {
    int bitIndex = bitIndices[i];
    int wordIndex = bitIndex / 16;
    int position = bitIndex % 16;
    noisy.w[wordIndex] ^= (1 << position);
  }
  return noisy;
}

} // namespace hashing
} // namespace pdq
} // namespace facebook
