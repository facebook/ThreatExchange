// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <vpdq/cpp/hashing/bufferhasher.h>

namespace facebook {
namespace vpdq {
namespace hashing {

AbstractFrameBufferHasher::AbstractFrameBufferHasher(
    int frameHeight, int frameWidth)
    : _frameHeight(frameHeight),
      _frameWidth(frameWidth),
      _numRGBTriples(frameHeight * frameWidth) {}

} // namespace hashing
} // namespace vpdq
} // namespace facebook
