// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#ifndef FILEHASHER_H
#define FILEHASHER_H

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/io/tmkio.h>

namespace facebook {
namespace tmk {
namespace hashing {

bool hashVideoFile(
    const std::string& inputVideoFileName,
    facebook::tmk::io::TMKFramewiseAlgorithm tmkFramewiseAlgorithm,
    const std::string& ffmpegPath,
    int resampleFramesPerSecond,
    facebook::tmk::algo::TMKFeatureVectors& output,
    bool verbose,
    const char* argv0);

bool hashEverstoreVideoFile(
    const std::string& inputEverstoreHandle,
    io::TMKFramewiseAlgorithm tmkFramewiseAlgorithm,
    const std::string& ffmpegPath,
    const std::string& everstorePath,
    int resampleFramesPerSecond,
    facebook::tmk::algo::TMKFeatureVectors& tmkFeatureVectors,
    bool verbose,
    const char* argv0);

} // namespace hashing
} // namespace tmk
} // namespace facebook

#endif // FILEHASHER_H
