// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef VPDQIO_H
#define VPDQIO_H

#include <pdq/cpp/common/pdqhashtypes.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>

#include <vector>

namespace facebook {
namespace vpdq {
namespace io {

bool loadHashesFromFileOrDie(
    const std::string& inputHashFileName,
    std::vector<hashing::vpdqFeature>& pdqHashes);
bool outputVPDQFeatureToFile(
    const std::string& outputHashFileName,
    const std::vector<hashing::vpdqFeature>& pdqHashes);
} // namespace io
} // namespace vpdq
} // namespace facebook
#endif // VPDQIO_H
