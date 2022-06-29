#include <vpdq/cpp/hashing/vpdqHashType.h>

#ifndef MATCHTWOHASH_H
#define MATCHTWOHASH_H

using namespace std;

namespace facebook {
namespace vpdq {
namespace hashing {
/**
 * Compare two vpdq hash vectors in brute-force.
 * Result in two float percentage number qMatch, tMatch
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
    vector<vpdq::hashing::vpdqFeature> qHashes,
    vector<vpdq::hashing::vpdqFeature> tHashes,
    int distanceTolerance,
    int qualityTolerance,
    double& qMatch,
    double& tMatch,
    bool verbose);
} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // MATCHTWOHASH_H
