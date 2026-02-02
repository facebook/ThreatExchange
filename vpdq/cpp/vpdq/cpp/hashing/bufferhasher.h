// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef BUFFERHASHER_H
#define BUFFERHASHER_H

#include <memory>
#include <string>
#include <vector>
#include <pdq/cpp/common/pdqhashtypes.h>
#include <pdq/cpp/hashing/pdqhashing.h>

namespace facebook {
namespace vpdq {
namespace hashing {

/**
 *
 * Abstract FrameBufferHasher class
 *
 * @param frameHeight Input frame's height
 * @param frameWidth Input frame's width
 *
 */
class AbstractFrameBufferHasher {
 protected:
  int _frameHeight;
  int _frameWidth;
  int _numRGBTriples;

 public:
  AbstractFrameBufferHasher(int frameHeight, int frameWidth) {
    _frameHeight = frameHeight;
    _frameWidth = frameWidth;
    _numRGBTriples = frameHeight * frameWidth;
  }
  virtual ~AbstractFrameBufferHasher() {}

  // Number of floats in each framewise hash
  virtual int getFeatureDimension() = 0;

  virtual bool hashFrame(
      unsigned char* buffer,
      int linesize,
      pdq::hashing::Hash256& hash,
      int& quality) = 0;
};

/**
 *
 * PDQ Hash FrameBufferHasher class which inherits AbstractFrameBufferHasher
 *
 * @param frameHeight Input frame's height
 * @param frameWidth Input frame's height
 *
 */
class PDQFrameBufferHasher : public AbstractFrameBufferHasher {
 private:
  //  Variables for computing pdq hash
  std::vector<float> _fullLumaImageBuffer1;
  std::vector<float> _fullLumaImageBuffer2;
  static const int SCALED_DIMENSION = 64;
  float _buffer64x64[64][64];
  float _buffer16x64[16][64];
  float _buffer16x16[16][16];

 public:
  PDQFrameBufferHasher(int frameHeight, int frameWidth)
      : AbstractFrameBufferHasher(frameHeight, frameWidth) {
    _fullLumaImageBuffer1 = std::vector<float>(_numRGBTriples);
    _fullLumaImageBuffer2 = std::vector<float>(_numRGBTriples);
  }

  ~PDQFrameBufferHasher() {}

  static int getFrameDownscaleDimension() { return SCALED_DIMENSION; }
  int getFeatureDimension() override { return pdq::hashing::HASH256_NUM_BITS; }
  // Get PDQ Hash in Hash256 format
  bool hashFrame(
      unsigned char* buffer,
      int linesize,
      pdq::hashing::Hash256& hash,
      int& quality) override;
};

// A factory design pattern to create the Buffer Hasher
class FrameBufferHasherFactory {
 public:
  static int getFrameHasherDownscaleDimension();
  static std::unique_ptr<AbstractFrameBufferHasher> createFrameHasher(
      int frameHeight, int frameWidth);
};

} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // BUFFERHASHER_H
