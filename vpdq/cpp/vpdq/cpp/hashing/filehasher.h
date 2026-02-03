// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef VPDQ_HASHING_FILEHASHER_H
#define VPDQ_HASHING_FILEHASHER_H

#include <vpdq/cpp/hashing/vpdqHashType.h>

#include <string>
#include <vector>

namespace facebook {
namespace vpdq {
namespace hashing {

/**
 * @brief Hashes the video file using the vpdq hashing algorithm.
 *
 * @param inputVideoFileName Input video path.
 * @param pdqHashes Resulting vector that will contain the vpdq hash.
 * @param verbose Output details for diagnostic purposes.
 * @param secondsPerHash The interval for frame hashing.
 * @param downsampleWidth Width to downsample to before hashing. 0 means no
 *                        downsample
 * @param downsampleHeight Height to downsample to before hashing. 0 means no
 *                         downsample
 * @param num_threads Number of threads to use for hashing. 0 is auto.
 *
 * @return Video hashed successfully.
 */
bool hashVideoFile(
    const std::string& inputVideoFileName,
    std::vector<facebook::vpdq::hashing::vpdqFeature>& pdqHashes,
    bool verbose = false,
    const double secondsPerHash = 1,
    const int downsampleWidth = 0,
    const int downsampleHeight = 0,
    const unsigned int num_threads = 0);

} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // VPDQ_HASHING_FILEHASHER_H
