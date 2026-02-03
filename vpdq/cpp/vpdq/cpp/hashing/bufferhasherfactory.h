// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef BUFFERHASHERFACTORY_H
#define BUFFERHASHERFACTORY_H

#include <vpdq/cpp/hashing/bufferhasher.h>

#include <memory>

namespace facebook {
namespace vpdq {
namespace hashing {

/** @brief A factory class to create the Buffer Hasher. */
class FrameBufferHasherFactory {
 public:
  static std::unique_ptr<AbstractFrameBufferHasher> createFrameHasher(
      int frameHeight, int frameWidth);

  static int getFrameHasherDownscaleDimension();
};

} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // BUFFERHASHERFACTORY_H
