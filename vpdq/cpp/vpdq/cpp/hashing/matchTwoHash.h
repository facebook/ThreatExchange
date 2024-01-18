// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef MATCHTWOHASH_H
#define MATCHTWOHASH_H

#include <vector>
#include <vpdq/cpp/hashing/vpdqHashType.h>

namespace facebook {
namespace vpdq {
namespace hashing {
/**
 * Compare two vpdq hash vectors in brute-force.
 * Result in two double percentages: qMatch, tMatch
 *
 * @param qHashes Query video's hash
 * @param tHashes Target video's hash
 * @param distanceTolerance Distance tolerance of considering a match
 * @param qualityTolerance Quality tolerance of comparing two hash. If lower
 * than the tolerance, will skip comparing.
 * @param qMatch Percentage of matches in query hash
 * @param tMatch Percentage of matches in target hash
 * @param verbose If produce detailed output for diagnostic purposes
 * @param programName The name of executable program which invokes the function
 *
 * @return If successfully hash the video
 */
bool matchTwoHashBrute(
    std::vector<vpdq::hashing::vpdqFeature> qHashes,
    std::vector<vpdq::hashing::vpdqFeature> tHashes,
    const int distanceTolerance,
    const int qualityTolerance,
    double& qMatch,
    double& tMatch,
    const bool verbose);
} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // MATCHTWOHASH_H
