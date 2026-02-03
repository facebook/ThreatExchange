// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef PDQBUFFERHASHER_H
#define PDQBUFFERHASHER_H

#include <pdq/cpp/common/pdqhashtypes.h>
#include <vpdq/cpp/hashing/bufferhasher.h>

#include <vector>

namespace facebook {
namespace vpdq {
namespace hashing {

/**
 * @brief
 * A frame buffer hasher that uses the PDQ algorithm to generate perceptual
 * hashes for a frame.
 */
class PDQFrameBufferHasher : public AbstractFrameBufferHasher {
 public:
  /**
   * @brief Constructor.
   *
   * @param frameHeight Input frame's height.
   * @param frameWidth Input frame's width.
   */
  PDQFrameBufferHasher(int frameHeight, int frameWidth);

  ~PDQFrameBufferHasher() = default;

  int getFeatureDimension() const override;

  bool hashFrame(
      unsigned char* buffer,
      int linesize,
      facebook::pdq::hashing::Hash256& hash,
      int& quality) override;

  static constexpr int getFrameDownscaleDimension() { return 64; }

  // Copy
  PDQFrameBufferHasher(const PDQFrameBufferHasher&) = default;
  PDQFrameBufferHasher& operator=(const PDQFrameBufferHasher&) = default;

  // Move
  PDQFrameBufferHasher(PDQFrameBufferHasher&&) = default;
  PDQFrameBufferHasher& operator=(PDQFrameBufferHasher&&) = default;

 private:
  // Variables for computing pdq hash
  std::vector<float> _fullLumaImageBuffer1;
  std::vector<float> _fullLumaImageBuffer2;
  float _buffer64x64[64][64];
  float _buffer16x64[16][64];
  float _buffer16x16[16][16];
};

} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // PDQBUFFERHASHER_H
