// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <iostream>

#include <pdq/cpp/io/hashio.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>
#include <vpdq/cpp/io/vpdqio.h>

namespace facebook {
namespace vpdq {
namespace hashing {

/**
 * @brief Filter low quality hashes from a feature vector
 *
 * @param features Features to filter
 * @param qualityTolerance Quality tolerance of comparing two hashes. If lower
 * then it won't be included in the result
 * @param verbose Print skipped hashes
 *
 * @return Feature vector without features with quality lower than
 * qualityTolerance
 */
static std::vector<vpdq::hashing::vpdqFeature> filterFeatures(
    const std::vector<vpdq::hashing::vpdqFeature>& features,
    const int qualityTolerance,
    const bool verbose) {
  std::vector<vpdq::hashing::vpdqFeature> filteredHashes;
  for (const auto& feature : features) {
    if (feature.quality >= qualityTolerance) {
      filteredHashes.push_back(feature);
    } else if (verbose) {
      auto index = &feature - &features[0];
      std::cout << "Skipping Line " << index
                << " Skipping Hash: " << feature.pdqHash.format()
                << ", because of low quality: " << feature.quality << std::endl;
    }
  }
  return filteredHashes;
}

/**
 * @brief Get the number of matches between two feature vectors
 *
 * @param features1 Features to match
 * @param features2 Features to match
 * @param distanceTolerance Distance tolerance of considering a match. Lower is
 * more similar.
 * @param verbose Print features with matching hashes
 *
 * @return Number of matches
 */
static std::vector<vpdq::hashing::vpdqFeature>::size_type findMatches(
    const std::vector<vpdq::hashing::vpdqFeature>& features1,
    const std::vector<vpdq::hashing::vpdqFeature>& features2,
    const int distanceTolerance,
    const bool verbose) {
  unsigned int matchCnt = 0;
  for (const auto& feature1 : features1) {
    for (const auto& feature2 : features2) {
      if (feature1.pdqHash.hammingDistance(feature2.pdqHash) <
          distanceTolerance) {
        matchCnt++;
        if (verbose) {
          std::cout << "Query Hash: " << feature1.pdqHash.format()
                    << " Target Hash: " << feature2.pdqHash.format()
                    << " match " << std::endl;
        }
        break;
      }
    }
  }
  return matchCnt;
}

bool matchTwoHashBrute(
    std::vector<vpdq::hashing::vpdqFeature> qHashes,
    std::vector<vpdq::hashing::vpdqFeature> tHashes,
    const int distanceTolerance,
    const int qualityTolerance,
    double& qMatch,
    double& tMatch,
    const bool verbose) {
  // Filter low quality hashes
  auto queryFiltered = filterFeatures(qHashes, qualityTolerance, verbose);
  auto targetFiltered = filterFeatures(tHashes, qualityTolerance, verbose);

  // Get count of query in target and target in query
  auto qMatchCnt =
      findMatches(queryFiltered, targetFiltered, distanceTolerance, verbose);
  auto tMatchCnt =
      findMatches(targetFiltered, queryFiltered, distanceTolerance, verbose);

  qMatch = (qMatchCnt * 100.0) / queryFiltered.size();
  tMatch = (tMatchCnt * 100.0) / targetFiltered.size();
  return true;
}
} // namespace hashing
} // namespace vpdq
} // namespace facebook
