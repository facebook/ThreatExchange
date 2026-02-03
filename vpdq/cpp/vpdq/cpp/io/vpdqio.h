// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef VPDQIO_H
#define VPDQIO_H

#include <vpdq/cpp/hashing/vpdqHashType.h>

#include <string>
#include <vector>

namespace facebook {
namespace vpdq {
namespace io {

bool loadHashesFromFileOrDie(
    const std::string& inputHashFileName,
    std::vector<facebook::vpdq::hashing::vpdqFeature>& vpdqHashes);

bool outputVPDQFeatureToFile(
    const std::string& outputHashFileName,
    const std::vector<facebook::vpdq::hashing::vpdqFeature>& vpdqHashes);

} // namespace io
} // namespace vpdq
} // namespace facebook

#endif // VPDQIO_H
