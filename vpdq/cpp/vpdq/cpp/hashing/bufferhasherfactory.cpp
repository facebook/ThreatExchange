// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <vpdq/cpp/hashing/bufferhasherfactory.h>

#include <vpdq/cpp/hashing/bufferhasher.h>
#include <vpdq/cpp/hashing/pdqbufferhasher.h>

#include <memory>

namespace facebook {
namespace vpdq {
namespace hashing {

std::unique_ptr<AbstractFrameBufferHasher>
FrameBufferHasherFactory::createFrameHasher(int frameHeight, int frameWidth) {
  return std::make_unique<PDQFrameBufferHasher>(frameHeight, frameWidth);
}

int FrameBufferHasherFactory::getFrameHasherDownscaleDimension() {
  return PDQFrameBufferHasher::getFrameDownscaleDimension();
}

} // namespace hashing
} // namespace vpdq
} // namespace facebook
