// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef MATCHTWOHASH_H
#define MATCHTWOHASH_H

#include <vpdq/cpp/hashing/vpdqHashType.h>

#include <vector>

namespace facebook {
namespace vpdq {
namespace hashing {

/**
 * @brief
 * Compare two vpdq hash vectors in brute-force.
 * Result in two double percentages: qMatch, tMatch
 *
 * @param qHashes The query video perceptual hash
 * @param tHashes The target video perceptual hash
 * @param distanceTolerance Distance tolerance of considering a match
 *
 * @param qualityTolerance Quality tolerance of comparing two hash. If lower
 *                         than the tolerance, will skip comparing.
 *
 * @param[out] qMatch Result percentage of matches in query hash
 * @param[out] tMatch Result percentage of matches in target hash
 * @param verbose Produce detailed output for diagnostic purposes
 */
void matchTwoHashBrute(
    const std::vector<vpdq::hashing::vpdqFeature>& qHashes,
    const std::vector<vpdq::hashing::vpdqFeature>& tHashes,
    const int distanceTolerance,
    const int qualityTolerance,
    double& qMatch,
    double& tMatch,
    const bool verbose);

} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // MATCHTWOHASH_H
