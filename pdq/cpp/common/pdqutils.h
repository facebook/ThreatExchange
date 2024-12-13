#ifndef PDQ_UTILS_H
#define PDQ_UTILS_H

#include <pdq/cpp/common/pdqhashtypes.h>
#include <random>
#include <vector>

namespace facebook {
namespace pdq {
namespace hashing {

  // Generate random hash
  Hash256 generateRandomHash(std::mt19937& gen);

  // Add noise to hash by flipping random bits
  Hash256 addNoise(
      const Hash256& original,
      int numBitsToFlip,
      std::mt19937& gen);

} // namespace hashing
} // namespace pdq
} // namespace facebook

#endif