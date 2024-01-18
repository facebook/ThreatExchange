// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <mutex>

#include <pdq/cpp/downscaling/downscaling.h>
#include <pdq/cpp/hashing/pdqhashing.h>
#include <pdq/cpp/hashing/torben.h>

// ================================================================
// PDQ algorithm description:
// https://github.com/facebookexternal/ThreatExchange-PDQ/blob/main/pdqhash-2017-10-09.pdf
// ================================================================

#if defined(_WIN32)
#define _USE_MATH_DEFINES
#endif

#include <cassert>
#include <chrono>
#include <cmath>

using namespace std;

namespace facebook {
namespace pdq {
namespace hashing {

//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// From Wikipedia: standard RGB to luminance (the 'Y' in 'YUV').
const float luma_from_R_coeff = 0.299;
const float luma_from_G_coeff = 0.587;
const float luma_from_B_coeff = 0.114;

//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Minimum size tested.
const int MIN_HASHABLE_DIM = 5;

//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Tent filter.
const int PDQ_NUM_JAROSZ_XY_PASSES = 2;

//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Christoph Zauner 'Implementation and Benchmarking of Perceptual
// Image Hash Functions' 2010
static float* fill_dct_matrix_64_cached();

// ----------------------------------------------------------------
void fillFloatLumaFromRGB(
    uint8_t* pRbase,
    uint8_t* pGbase,
    uint8_t* pBbase,
    int numRows,
    int numCols,
    int rowStride,
    int colStride,
    float* luma // numRows x numCols, row-major
) {
  uint8_t* pRrow = pRbase;
  uint8_t* pGrow = pGbase;
  uint8_t* pBrow = pBbase;
  for (int i = 0; i < numRows; i++) {
    uint8_t* pR = pRrow;
    uint8_t* pG = pGrow;
    uint8_t* pB = pBrow;
    for (int j = 0; j < numCols; j++) {
      float yval = luma_from_R_coeff * (*pR) + luma_from_G_coeff * (*pG) +
          luma_from_B_coeff * (*pB);
      luma[i * numCols + j] = yval;
      pR += colStride;
      pG += colStride;
      pB += colStride;
    }
    pRrow += rowStride;
    pGrow += rowStride;
    pBrow += rowStride;
  }
}

// ----------------------------------------------------------------
void fillFloatLumaFromGrey(
    uint8_t* pbase,
    int numRows,
    int numCols,
    int rowStride,
    int colStride,
    float* luma // numRows x numCols, row-major
) {
  uint8_t* prow = pbase;
  for (int i = 0; i < numRows; i++) {
    uint8_t* p = prow;
    for (int j = 0; j < numCols; j++) {
      luma[i * numCols + j] = (float)(*p);
      p += colStride;
    }
    prow += rowStride;
  }
}

// ----------------------------------------------------------------
void pdqHash256FromFloatLuma(
    float* fullBuffer1, // numRows x numCols, row-major
    float* fullBuffer2, // numRows x numCols, row-major
    int numRows,
    int numCols,
    float buffer64x64[64][64],
    float buffer16x64[16][64],
    float buffer16x16[16][16],
    Hash256& hash,
    int& quality) {
  if (numRows < MIN_HASHABLE_DIM || numCols < MIN_HASHABLE_DIM) {
    hash.clear();
    quality = 0;
    return;
  }

  pdqFloat256FromFloatLuma(
      fullBuffer1,
      fullBuffer2,
      numRows,
      numCols,
      buffer64x64,
      buffer16x64,
      buffer16x16,
      quality);

  // Output bits
  pdqBuffer16x16ToBits(buffer16x16, &hash);
}

// ----------------------------------------------------------------
void pdqFloat256FromFloatLuma(
    float* fullBuffer1, // numRows x numCols, row-major
    float* fullBuffer2, // numRows x numCols, row-major
    int numRows,
    int numCols,
    float buffer64x64[64][64],
    float buffer16x64[16][64],
    float output_buffer16x16[16][16],
    int& quality) {
  if (numRows == 64 && numCols == 64) {
    // E.g. for video-frame processing when we've already used ffmpeg
    // to downsample for us.
    int i, j, k;
    for (k = 0, i = 0; i < 64; i++) {
      for (j = 0; j < 64; j++, k++) {
        buffer64x64[i][j] = fullBuffer1[k];
      }
    }
  } else {
    // Downsample (blur and decimate)
    int windowSizeAlongRows =
        facebook::pdq::downscaling::computeJaroszFilterWindowSize(numCols, 64);
    int windowSizeAlongCols =
        facebook::pdq::downscaling::computeJaroszFilterWindowSize(numRows, 64);

    facebook::pdq::downscaling::jaroszFilterFloat(
        fullBuffer1,
        fullBuffer2,
        numRows,
        numCols,
        windowSizeAlongRows,
        windowSizeAlongCols,
        PDQ_NUM_JAROSZ_XY_PASSES);

    facebook::pdq::downscaling::decimateFloat(
        fullBuffer1, numRows, numCols, &buffer64x64[0][0], 64, 64);
  }

  // Quality metric.  Reuse the 64x64 image-domain downsample
  // since we already have it.
  quality = pdqImageDomainQualityMetric(buffer64x64);

  // 2D DCT
  dct64To16(buffer64x64, buffer16x64, output_buffer16x16);
}

// ----------------------------------------------------------------
bool pdqDihedralHash256esFromFloatLuma(
    float* fullBuffer1, // numRows x numCols, row-major
    float* fullBuffer2, // numRows x numCols, row-major
    int numRows,
    int numCols,
    float buffer64x64[64][64],
    float buffer16x64[16][64],
    float buffer16x16[16][16],
    float buffer16x16Aux[16][16],
    Hash256* hashptrOriginal,
    Hash256* hashptrRotate90,
    Hash256* hashptrRotate180,
    Hash256* hashptrRotate270,
    Hash256* hashptrFlipX,
    Hash256* hashptrFlipY,
    Hash256* hashptrFlipPlus1,
    Hash256* hashptrFlipMinus1,
    int& quality) {
  if (numRows < MIN_HASHABLE_DIM || numCols < MIN_HASHABLE_DIM) {
    if (hashptrOriginal != nullptr) {
      hashptrOriginal->clear();
    }
    if (hashptrRotate90 != nullptr) {
      hashptrRotate90->clear();
    }
    if (hashptrRotate180 != nullptr) {
      hashptrRotate180->clear();
    }
    if (hashptrRotate270 != nullptr) {
      hashptrRotate270->clear();
    }
    if (hashptrFlipX != nullptr) {
      hashptrFlipX->clear();
    }
    if (hashptrFlipY != nullptr) {
      hashptrFlipY->clear();
    }
    if (hashptrFlipPlus1 != nullptr) {
      hashptrFlipPlus1->clear();
    }
    if (hashptrFlipMinus1 != nullptr) {
      hashptrFlipMinus1->clear();
    }
    quality = 0;
    return true;
  }

  // Downsample (blur and decimate)
  int windowSizeAlongRows =
      facebook::pdq::downscaling::computeJaroszFilterWindowSize(numCols, 64);
  int windowSizeAlongCols =
      facebook::pdq::downscaling::computeJaroszFilterWindowSize(numRows, 64);

  facebook::pdq::downscaling::jaroszFilterFloat(
      fullBuffer1,
      fullBuffer2,
      numRows,
      numCols,
      windowSizeAlongRows,
      windowSizeAlongCols,
      PDQ_NUM_JAROSZ_XY_PASSES);

  facebook::pdq::downscaling::decimateFloat(
      fullBuffer1, numRows, numCols, &buffer64x64[0][0], 64, 64);

  // Quality metric.  Reuse the 64x64 image-domain downsample
  // since we already have it.
  quality = pdqImageDomainQualityMetric(buffer64x64);

  // 2D DCT
  dct64To16(buffer64x64, buffer16x64, buffer16x16);

  //  Output bits
  if (hashptrOriginal != nullptr) {
    pdqBuffer16x16ToBits(buffer16x16, hashptrOriginal);
  }
  if (hashptrRotate90 != nullptr) {
    dct16OriginalToRotate90(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrRotate90);
  }
  if (hashptrRotate180 != nullptr) {
    dct16OriginalToRotate180(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrRotate180);
  }
  if (hashptrRotate270 != nullptr) {
    dct16OriginalToRotate270(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrRotate270);
  }
  if (hashptrFlipX != nullptr) {
    dct16OriginalToFlipX(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrFlipX);
  }
  if (hashptrFlipY != nullptr) {
    dct16OriginalToFlipY(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrFlipY);
  }
  if (hashptrFlipPlus1 != nullptr) {
    dct16OriginalToFlipPlus1(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrFlipPlus1);
  }
  if (hashptrFlipMinus1 != nullptr) {
    dct16OriginalToFlipMinus1(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrFlipMinus1);
  }

  return true;
}

// ----------------------------------------------------------------
// This is all heuristic (see the PDQ hashing doc). Quantization matters since
// we want to count *significant* gradients, not just the some of many small
// ones. The constants are all manually selected, and tuned as described in the
// document.
int pdqImageDomainQualityMetric(float buffer64x64[64][64]) {
  int gradient_sum = 0;

  for (int i = 0; i < 63; i++) {
    for (int j = 0; j < 64; j++) {
      float u = buffer64x64[i][j];
      float v = buffer64x64[i + 1][j];
      int d = ((u - v) * 100) / 255;
      gradient_sum += (int)std::abs(d);
    }
  }
  for (int i = 0; i < 64; i++) {
    for (int j = 0; j < 63; j++) {
      float u = buffer64x64[i][j];
      float v = buffer64x64[i][j + 1];
      int d = ((u - v) * 100) / 255;
      gradient_sum += (int)std::abs(d);
    }
  }

  // Heuristic scaling factor.
  int quality = gradient_sum / 90;
  if (quality > 100) {
    quality = 100;
  }

  return quality;
}

// ----------------------------------------------------------------
// Full 64x64 to 64x64 can be optimized e.g. the Lee algorithm.  But here we
// only want slots (1-16)x(1-16) of the full 64x64 output. Careful experiments
// showed that using Lee along all 64 slots in one dimension, then Lee along 16
// slots in the second, followed by extracting slots 1-16 of the output, was
// actually slower than the current implementation which is completely
// non-clever/non-Lee but computes only what is needed.

void dct64To16(float A[64][64], float T[16][64], float B[16][16]) {
  // DCT matrix:
  // * numRows is 16.
  // * numCols is 64.
  // * Storage is row-major
  // * Element i,j at row i column j is at offset i*16+j.
  float* D = fill_dct_matrix_64_cached();

  // B = D A Dt
  // B = (D A) Dt
  // with intermediate T = D A

  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 64; j++) {
      float* pd = &D[i * 64]; // ith row
      float* pa = &A[0][j];
      float sumk = 0.0;

      for (int k = 0; k < 64;) {
        sumk += pd[k++] * pa[0];
        sumk += pd[k++] * pa[1 << 6];
        sumk += pd[k++] * pa[2 << 6];
        sumk += pd[k++] * pa[3 << 6];
        sumk += pd[k++] * pa[4 << 6];
        sumk += pd[k++] * pa[5 << 6];
        sumk += pd[k++] * pa[6 << 6];
        sumk += pd[k++] * pa[7 << 6];
        sumk += pd[k++] * pa[8 << 6];
        sumk += pd[k++] * pa[9 << 6];
        sumk += pd[k++] * pa[10 << 6];
        sumk += pd[k++] * pa[11 << 6];
        sumk += pd[k++] * pa[12 << 6];
        sumk += pd[k++] * pa[13 << 6];
        sumk += pd[k++] * pa[14 << 6];
        sumk += pd[k++] * pa[15 << 6];
        pa += 1024;
      }
      T[i][j] = sumk;
    }
  }

  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      float sumk = 0.0;
      float* pd = &D[j * 64]; // jth row
      float* pt = &T[i][0];
      for (int k = 0; k < 64;) {
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
        sumk += pt[k] * pd[k];
        k++;
      }
      B[i][j] = sumk;
    }
  }
}

// ----------------------------------------------------------------
// orig      rot90     rot180    rot270
// noxpose   xpose     noxpose   xpose
// + + + +   - + - +   + - + -   - - - -
// + + + +   - + - +   - + - +   + + + +
// + + + +   - + - +   + - + -   - - - -
// + + + +   - + - +   - + - +   + + + +
//
// flipx     flipy     flipplus  flipminus
// noxpose   noxpose   xpose     xpose
// - - - -   - + - +   + + + +   + - + -
// + + + +   - + - +   + + + +   - + - +
// - - - -   - + - +   + + + +   + - + -
// + + + +   - + - +   + + + +   - + - +

// ----------------------------------------------------------------
void dct16OriginalToRotate90(float A[16][16], float B[16][16]) {
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      if (j & 1) {
        B[j][i] = A[i][j];
      } else {
        B[j][i] = -A[i][j];
      }
    }
  }
}

void dct16OriginalToRotate180(float A[16][16], float B[16][16]) {
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      if ((i + j) & 1) {
        B[i][j] = -A[i][j];
      } else {
        B[i][j] = A[i][j];
      }
    }
  }
}

void dct16OriginalToRotate270(float A[16][16], float B[16][16]) {
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      if (i & 1) {
        B[j][i] = A[i][j];
      } else {
        B[j][i] = -A[i][j];
      }
    }
  }
}

void dct16OriginalToFlipX(float A[16][16], float B[16][16]) {
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      if (i & 1) {
        B[i][j] = A[i][j];
      } else {
        B[i][j] = -A[i][j];
      }
    }
  }
}

void dct16OriginalToFlipY(float A[16][16], float B[16][16]) {
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      if (j & 1) {
        B[i][j] = A[i][j];
      } else {
        B[i][j] = -A[i][j];
      }
    }
  }
}

void dct16OriginalToFlipPlus1(float A[16][16], float B[16][16]) {
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      B[j][i] = A[i][j];
    }
  }
}

void dct16OriginalToFlipMinus1(float A[16][16], float B[16][16]) {
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      if ((i + j) & 1) {
        B[j][i] = -A[i][j];
      } else {
        B[j][i] = A[i][j];
      }
    }
  }
}

// ----------------------------------------------------------------
// Each bit of the 16x16 output hash is for whether the given frequency
// component is greater than the median frequency component or not.
void pdqBuffer16x16ToBits(float dctOutput16x16[16][16], Hash256* hashptr) {
  float dct_median = torben(&dctOutput16x16[0][0], 16 * 16);

  hashptr->clear();
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      if (dctOutput16x16[i][j] > dct_median) {
        hashptr->setBit(i * 16 + j);
      }
    }
  }
}

// ----------------------------------------------------------------
// See comments on dct64To16. Input is (0..63)x(0..63); output is
// (1..16)x(1..16) with the latter indexed as (0..15)x(0..15).
//
// * numRows is 16.
// * numCols is 64.
// * Storage is row-major
// * Element i,j at row i column j is at offset i*16+j.
static float* fill_dct_matrix_64_cached() {
  static std::once_flag initialized;
  static float buffer[16 * 64];

  std::call_once(initialized, []() {
    const float matrix_scale_factor = std::sqrt(2.0 / 64.0);
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 64; j++) {
        buffer[i * 64 + j] = matrix_scale_factor *
            cos((M_PI / 2 / 64.0) * (i + 1) * (2 * j + 1));
      }
    }
  });
  return &buffer[0];
}

} // namespace hashing
} // namespace pdq
} // namespace facebook
