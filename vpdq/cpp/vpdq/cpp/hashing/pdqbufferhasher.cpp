// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <vpdq/cpp/hashing/pdqbufferhasher.h>

#include <pdq/cpp/common/pdqhashtypes.h>
#include <pdq/cpp/hashing/pdqhashing.h>
#include <vpdq/cpp/hashing/bufferhasher.h>

#include <vector>

namespace facebook {
namespace vpdq {
namespace hashing {

static constexpr int MIN_HASHABLE_DIM = 5;

bool PDQFrameBufferHasher::hashFrame(
    unsigned char* buffer,
    int linesize,
    facebook::pdq::hashing::Hash256& hash, // The result pdq hash
    int& quality // Hashing Quality
) {
  if (_frameHeight < MIN_HASHABLE_DIM || _frameWidth < MIN_HASHABLE_DIM ||
      linesize < (_frameWidth * 3)) {
    hash.clear();
    quality = 0;
    return false;
  }
  facebook::pdq::hashing::fillFloatLumaFromRGB(
      &buffer[0], // pRbase
      &buffer[1], // pGbase
      &buffer[2], // pBbase
      _frameHeight,
      _frameWidth,
      linesize, // rowStride
      3, // colStride
      _fullLumaImageBuffer1.data());

  facebook::pdq::hashing::pdqHash256FromFloatLuma(
      _fullLumaImageBuffer1.data(), // numRows x numCols, row-major
      _fullLumaImageBuffer2.data(), // numRows x numCols, row-major
      _frameHeight,
      _frameWidth,
      _buffer64x64,
      _buffer16x64,
      _buffer16x16,
      hash,
      quality);

  return true;
}

PDQFrameBufferHasher::PDQFrameBufferHasher(int frameHeight, int frameWidth)
    : AbstractFrameBufferHasher(frameHeight, frameWidth),
      _fullLumaImageBuffer1(std::vector<float>(_numRGBTriples)),
      _fullLumaImageBuffer2(std::vector<float>(_numRGBTriples)) {}

int PDQFrameBufferHasher::getFeatureDimension() const {
  return facebook::pdq::hashing::HASH256_NUM_BITS;
}

} // namespace hashing
} // namespace vpdq
} // namespace facebook
