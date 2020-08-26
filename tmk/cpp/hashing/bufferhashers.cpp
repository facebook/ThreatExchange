// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// These map from RGB frame rasters (one per video frame) to frame-feature
// vectors (one per frame). Multiple frame-hashing algorithms are supported.
// ================================================================

#include <tmk/cpp/hashing/bufferhashers.h>
#include <pdq/cpp/downscaling/downscaling.h>
#include <stdio.h>

namespace facebook {
namespace tmk {
namespace hashing {

// ----------------------------------------------------------------
bool PDQFloatFrameBufferHasher::hashFrame(
    unsigned char* buffer,
    tmk::algo::FrameFeature& frameFeature // already allocated to our dimension
) {
  facebook::pdq::hashing::fillFloatLumaFromRGB(
      &buffer[0], // pRbase
      &buffer[1], // pGbase
      &buffer[2], // pBbase
      _frameHeight,
      _frameWidth,
      3 * _frameWidth, // rowStride
      3, // colStride
      _fullLumaImageBuffer1.data());

  int pdqQualityUnusedHere;
  facebook::pdq::hashing::pdqFloat256FromFloatLuma(
      _fullLumaImageBuffer1.data(), // numRows x numCols, row-major
      _fullLumaImageBuffer2.data(), // numRows x numCols, row-major
      _frameHeight,
      _frameWidth,
      _buffer64x64,
      _buffer16x64,
      _outputBuffer16x16,
      pdqQualityUnusedHere);

  float* q = &_outputBuffer16x16[0][0];
  int d = getFeatureDimension();
  for (int i = 0; i < d; i++) {
    frameFeature[i] = q[i];
  }

  return true;
}

// ----------------------------------------------------------------
int FrameBufferHasherFactory::getFrameHasherDownscaleDimension(
    io::TMKFramewiseAlgorithm algorithm) {
  int retval = 0;
  switch (algorithm) {
    case io::TMKFramewiseAlgorithm::PDQ_FLOAT:
      retval = PDQFloatFrameBufferHasher::getFrameDownscaleDimension();
      break;
    default:
      throw std::runtime_error(
          "FrameBufferHasherFactory: unmapped algorithm type " +
          std::to_string((int)algorithm));
      break;
  }
  return retval;
}

// ----------------------------------------------------------------
std::unique_ptr<AbstractFrameBufferHasher>
FrameBufferHasherFactory::createFrameHasher(
    io::TMKFramewiseAlgorithm algorithm,
    int frameHeight,
    int frameWidth) {
  std::unique_ptr<AbstractFrameBufferHasher> retval;
  switch (algorithm) {
    case io::TMKFramewiseAlgorithm::PDQ_FLOAT:
      retval =
          std::make_unique<PDQFloatFrameBufferHasher>(frameHeight, frameWidth);
      break;
    default:
      break;
  }
  return retval;
}

} // namespace hashing
} // namespace tmk
} // namespace facebook
