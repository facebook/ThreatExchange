// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef VPDQ_HASHING_BUFFERHASHER_H
#define VPDQ_HASHING_BUFFERHASHER_H

#include <pdq/cpp/common/pdqhashtypes.h>
#include <pdq/cpp/hashing/pdqhashing.h>

#include <memory>

namespace facebook {
namespace vpdq {
namespace hashing {

/**
 *
 * Abstract FrameBufferHasher class
 *
 * @param frameHeight Input frame's height
 * @param frameWidth Input frame's width
 */
class AbstractFrameBufferHasher {
 public:
  AbstractFrameBufferHasher(int frameHeight, int frameWidth);

  virtual ~AbstractFrameBufferHasher() = default;

  // Number of floats in each framewise hash
  virtual int getFeatureDimension() const = 0;

  // Get PDQ Hash in Hash256 format
  virtual bool hashFrame(
      unsigned char* buffer,
      int linesize,
      facebook::pdq::hashing::Hash256& hash,
      int& quality) = 0;

  // Copy
  AbstractFrameBufferHasher(const AbstractFrameBufferHasher&) = default;
  AbstractFrameBufferHasher& operator=(const AbstractFrameBufferHasher&) =
      default;

  // Move
  AbstractFrameBufferHasher(AbstractFrameBufferHasher&&) = default;
  AbstractFrameBufferHasher& operator=(AbstractFrameBufferHasher&&) = default;

 protected:
  int _frameHeight;
  int _frameWidth;
  int _numRGBTriples;
};

} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // VPDQ_HASHING_BUFFERHASHER_H
