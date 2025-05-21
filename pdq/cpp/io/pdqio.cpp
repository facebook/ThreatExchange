// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <pdq/cpp/downscaling/downscaling.h>
#include <pdq/cpp/hashing/pdqhashing.h>
#include <pdq/cpp/hashing/torben.h>

#include <math.h>
#include <stdlib.h>
#include <chrono>
#include "CImg.h"

using namespace std;
using namespace cimg_library;

namespace facebook {
namespace pdq {
namespace hashing {

// The two-pass Jarosz filter is prohibitively expensive for larger images
// so we use off-the-shelf downsampling to get to an intermediate size.
const int DOWNSAMPLE_DIMS = 512;

// ----------------------------------------------------------------
void showDecoderInfo() {
  cimg_library::cimg::info();
}

// ----------------------------------------------------------------
// Returns matrix as num_rows x num_cols in row-major order.
// The caller must free the return value.
float* loadFloatLumaFromCImg(CImg<uint8_t>& img, int& numRows, int& numCols) {
  if (img.spectrum() >= 3) {
    // X,Y,Z,color -> column,row,zero,{R,G,B}
    uint8_t* pr = &img(0, 0, 0, 0);
    uint8_t* pg = &img(0, 0, 0, 1);
    uint8_t* pb = &img(0, 0, 0, 2);

    numRows = img.height();
    numCols = img.width();

    int rowStride = &img(0, 1, 0, 0) - &img(0, 0, 0, 0);
    int colStride = &img(1, 0, 0, 0) - &img(0, 0, 0, 0);

    float* luma = new float[numRows * numCols];
    facebook::pdq::downscaling::fillFloatLumaFromRGB(
        pr, pg, pb, numRows, numCols, rowStride, colStride, luma);
    return luma;

  } else if (img.spectrum() == 1) {
    uint8_t* p = &img(0, 0, 0, 0);

    numRows = img.height();
    numCols = img.width();

    int rowStride = &img(0, 1, 0, 0) - &img(0, 0, 0, 0);
    int colStride = &img(1, 0, 0, 0) - &img(0, 0, 0, 0);

    // xxx cl
    float* luma = new float[numRows * numCols];
    facebook::pdq::downscaling::fillFloatLumaFromGrey(
        p, numRows, numCols, rowStride, colStride, luma);
    return luma;

  } else {
    fprintf(
        stderr,
        "Internal coding error detected at file %s line %d.\n",
        __FILE__,
        __LINE__);
    exit(1);
    return nullptr; // not reached
  }
}

// ----------------------------------------------------------------
bool pdqHash256FromFile(
    const char* filename,
    Hash256& hash,
    int& quality,
    int& imageHeightTimesWidth,
    float& readSeconds,
    float& hashSeconds) {
  chrono::time_point<chrono::system_clock> t1 = chrono::system_clock::now();

  if (!filename) {
    return false;
  }
  CImg<uint8_t> input;
  try {
    input.load(filename);
  } catch (const CImgIOException& ex) {
    return false;
  }

  chrono::time_point<chrono::system_clock> t2 = chrono::system_clock::now();
  chrono::duration<float> elapsed_seconds_outer = t2 - t1;
  readSeconds = elapsed_seconds_outer.count();

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  if (input.height() > DOWNSAMPLE_DIMS || input.width() > DOWNSAMPLE_DIMS) {
    input = input.resize(DOWNSAMPLE_DIMS, DOWNSAMPLE_DIMS);
  }
  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

  imageHeightTimesWidth = input.height() * input.width();

  t1 = chrono::system_clock::now();
  int numRows, numCols;
  float* fullBuffer1 = loadFloatLumaFromCImg(input, numRows, numCols);
  float* fullBuffer2 = new float[numRows * numCols];
  float buffer64x64[64][64];
  float buffer16x64[16][64];
  float buffer16x16[16][16];

  pdqHash256FromFloatLuma(
      fullBuffer1,
      fullBuffer2,
      numRows,
      numCols,
      buffer64x64,
      buffer16x64,
      buffer16x16,
      hash,
      quality);
  delete[] fullBuffer1;
  delete[] fullBuffer2;
  t2 = chrono::system_clock::now();
  elapsed_seconds_outer = t2 - t1;
  hashSeconds = elapsed_seconds_outer.count();

  return true;
}

// ----------------------------------------------------------------
bool pdqDihedralHash256esFromFile(
    const char* filename,
    Hash256* hashptrOriginal,
    Hash256* hashptrRotate90,
    Hash256* hashptrRotate180,
    Hash256* hashptrRotate270,
    Hash256* hashptrFlipX,
    Hash256* hashptrFlipY,
    Hash256* hashptrFlipPlus1,
    Hash256* hashptrFlipMinus1,
    int& quality,
    int& imageHeightTimesWidth,
    float& readSeconds,
    float& hashSeconds) {
  chrono::time_point<chrono::system_clock> t1 = chrono::system_clock::now();

  if (!filename) {
    return false;
  }
  CImg<uint8_t> input;
  try {
    input.load(filename);
  } catch (const CImgIOException& ex) {
    return false;
  }

  chrono::time_point<chrono::system_clock> t2 = chrono::system_clock::now();
  chrono::duration<float> elapsed_seconds_outer = t2 - t1;
  readSeconds = elapsed_seconds_outer.count();

  if (input.height() > DOWNSAMPLE_DIMS || input.width() > DOWNSAMPLE_DIMS) {
    input = input.resize(DOWNSAMPLE_DIMS, DOWNSAMPLE_DIMS);
  }

  imageHeightTimesWidth = input.height() * input.width();

  t1 = chrono::system_clock::now();
  int numRows, numCols;
  float* fullBuffer1 = loadFloatLumaFromCImg(input, numRows, numCols);
  float* fullBuffer2 = new float[numRows * numCols];
  float buffer64x64[64][64];
  float buffer16x64[16][64];
  float buffer16x16[16][16];
  float buffer16x16Aux[16][16];

  bool rv = pdqDihedralHash256esFromFloatLuma(
      fullBuffer1,
      fullBuffer2,
      numRows,
      numCols,
      buffer64x64,
      buffer16x64,
      buffer16x16,
      buffer16x16Aux,
      hashptrOriginal,
      hashptrRotate90,
      hashptrRotate180,
      hashptrRotate270,
      hashptrFlipX,
      hashptrFlipY,
      hashptrFlipPlus1,
      hashptrFlipMinus1,
      quality);

  delete[] fullBuffer1;
  delete[] fullBuffer2;
  t2 = chrono::system_clock::now();
  elapsed_seconds_outer = t2 - t1;
  hashSeconds = elapsed_seconds_outer.count();

  return rv;
}

// ----------------------------------------------------------------
// matrix as num_rows x num_cols in row-major order
void floatMatrixToCImg(
    float* matrix, int numRows, int numCols, const char filename[]) {
  CImg<float> cimg(numCols, numRows);
  for (int i = 0; i < numRows; i++) {
    for (int j = 0; j < numCols; j++) {
      cimg(j, i) = matrix[i * numCols + j];
    }
  }
  cimg.save(filename);
  printf("Saved tap %s\n", filename);
}

} // namespace hashing
} // namespace pdq
} // namespace facebook
