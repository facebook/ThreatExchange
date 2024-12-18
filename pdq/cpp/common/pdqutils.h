#ifndef PDQ_UTILS_H
#define PDQ_UTILS_H

#include <chrono>
#include <random>
#include <vector>
#include <pdq/cpp/common/pdqhashtypes.h>

class Timer {
 public:
  Timer(const std::string& context, bool printOnEnter = false);
  double elapsed() const;

 private:
  std::string context_;
  bool printOnEnter_;
  std::chrono::time_point<std::chrono::steady_clock> startTime_;
};

namespace facebook {
namespace pdq {
namespace hashing {

// Generate random hash
Hash256 generateRandomHash(std::mt19937& gen);

// Add noise to hash by flipping random bits
Hash256 addNoise(const Hash256& original, int numBitsToFlip, std::mt19937& gen);
} // namespace hashing
} // namespace pdq
} // namespace facebook
#endif
