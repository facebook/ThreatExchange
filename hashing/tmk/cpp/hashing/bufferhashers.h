// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// These map from RGB frame rasters (one per video frame) to frame-feature
// vectors (one per frame). Multiple frame-hashing algorithms are supported.
// ================================================================

#ifndef BUFFERHASHERS_H
#define BUFFERHASHERS_H

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/io/tmkio.h>

#include <pdq/cpp/hashing/pdqhashing.h>

#include <stdio.h>
#include <memory>
#include <string>
#include <vector>

namespace facebook {
namespace tmk {
namespace hashing {

// ----------------------------------------------------------------
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
      tmk::algo::FrameFeature& frameFeature) = 0;
};

// ----------------------------------------------------------------
class PDQFloatFrameBufferHasher : public AbstractFrameBufferHasher {
 private:
  std::vector<float> _fullLumaImageBuffer1;
  std::vector<float> _fullLumaImageBuffer2;
  static const int SCALED_DIMENSION = 64;
  float _buffer64x64[64][64];
  float _buffer16x64[16][64];
  float _outputBuffer16x16[16][16];

 public:
  PDQFloatFrameBufferHasher(int frameHeight, int frameWidth)
      : AbstractFrameBufferHasher(frameHeight, frameWidth) {
    _fullLumaImageBuffer1 = std::vector<float>(_numRGBTriples);
    _fullLumaImageBuffer2 = std::vector<float>(_numRGBTriples);
  }

  ~PDQFloatFrameBufferHasher() {}

  static int getFrameDownscaleDimension() {
    return SCALED_DIMENSION;
  }
  int getFeatureDimension() override {
    return facebook::pdq::hashing::HASH256_NUM_BITS;
  }

  bool hashFrame(unsigned char* buffer, tmk::algo::FrameFeature& frameFeature)
      override;
};

// ----------------------------------------------------------------
class FrameBufferHasherFactory {
 public:
  static int getFrameHasherDownscaleDimension(
      io::TMKFramewiseAlgorithm algorithm);
  static std::unique_ptr<AbstractFrameBufferHasher> createFrameHasher(
      io::TMKFramewiseAlgorithm algorithm,
      int frameHeight,
      int frameWidth);
};

} // namespace hashing
} // namespace tmk
} // namespace facebook

#endif // BUFFERHASHERS_H
