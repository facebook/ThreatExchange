// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include <pdq/cpp/common/pdqhashtypes.h>
#include <pdq/cpp/downscaling/downscaling.h>
#include <pdq/cpp/hashing/pdqhashing.h>
#include <vpdq/cpp/hashing/bufferhasher.h>

namespace facebook {
namespace vpdq {
namespace hashing {

const int MIN_HASHABLE_DIM = 5;

// ----------------------------------------------------------------
bool PDQFrameBufferHasher::hashFrame(
    unsigned char* buffer,
    int linesize,
    pdq::hashing::Hash256& hash, // The result pdq hash
    int& quality // Hashing Quality
) {
  if (_frameHeight < MIN_HASHABLE_DIM || _frameWidth < MIN_HASHABLE_DIM ||
      linesize < _frameWidth * 3) {
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

int FrameBufferHasherFactory::getFrameHasherDownscaleDimension() {
  return PDQFrameBufferHasher::getFrameDownscaleDimension();
  ;
}

// ----------------------------------------------------------------
std::unique_ptr<AbstractFrameBufferHasher>
FrameBufferHasherFactory::createFrameHasher(int frameHeight, int frameWidth) {
  return std::make_unique<PDQFrameBufferHasher>(frameHeight, frameWidth);
}

} // namespace hashing
} // namespace vpdq
} // namespace facebook
