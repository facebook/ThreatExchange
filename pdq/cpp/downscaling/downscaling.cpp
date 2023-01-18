// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include "downscaling.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include <chrono>

namespace facebook {
namespace pdq {
namespace downscaling {

//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// From Wikipedia: standard RGB to luminance (the 'Y' in 'YUV').
static const float luma_from_R_coeff = 0.299;
static const float luma_from_G_coeff = 0.587;
static const float luma_from_B_coeff = 0.114;

// ----------------------------------------------------------------
void fillFloatRGB(
    const uint8_t* pRbase,
    const uint8_t* pGbase,
    const uint8_t* pBbase,
    int numRows,
    int numCols,
    int rowStride,
    int colStride,
    float* pFloatR, // matrix as num_rows x num_cols in row-major order
    float* pFloatG, // matrix as num_rows x num_cols in row-major order
    float* pFloatB // matrix as num_rows x num_cols in row-major order
) {
  const uint8_t* pRrow = pRbase;
  const uint8_t* pGrow = pGbase;
  const uint8_t* pBrow = pBbase;
  for (int i = 0; i < numRows; i++) {
    const uint8_t* pR = pRrow;
    const uint8_t* pG = pGrow;
    const uint8_t* pB = pBrow;
    for (int j = 0; j < numCols; j++) {
      pFloatR[i * numCols + j] = (float)*pR;
      pFloatG[i * numCols + j] = (float)*pG;
      pFloatB[i * numCols + j] = (float)*pB;
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
void fillFloatRGBFromGrey(
    const uint8_t* pbase,
    int numRows,
    int numCols,
    int rowStride,
    int colStride,
    float* pFloatR, // matrix as num_rows x num_cols in row-major order
    float* pFloatG, // matrix as num_rows x num_cols in row-major order
    float* pFloatB // matrix as num_rows x num_cols in row-major order
) {
  const uint8_t* prow = pbase;
  for (int i = 0; i < numRows; i++) {
    const uint8_t* p = prow;
    for (int j = 0; j < numCols; j++) {
      pFloatR[i * numCols + j] = (float)*p;
      pFloatG[i * numCols + j] = (float)*p;
      pFloatB[i * numCols + j] = (float)*p;
      p += colStride;
    }
    prow += rowStride;
  }
}

// ----------------------------------------------------------------
void fillFloatLumaFromRGB(
    const uint8_t* pRbase,
    const uint8_t* pGbase,
    const uint8_t* pBbase,
    int numRows,
    int numCols,
    int rowStride,
    int colStride,
    float* luma // matrix as num_rows x num_cols in
                // row-major order
) {
  const uint8_t* pRrow = pRbase;
  const uint8_t* pGrow = pGbase;
  const uint8_t* pBrow = pBbase;
  for (int i = 0; i < numRows; i++) {
    const uint8_t* pR = pRrow;
    const uint8_t* pG = pGrow;
    const uint8_t* pB = pBrow;
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
    const uint8_t* pbase,
    int numRows,
    int numCols,
    int rowStride,
    int colStride,
    float* luma // matrix as num_rows x num_cols in
                // row-major order
) {
  const uint8_t* prow = pbase;
  for (int i = 0; i < numRows; i++) {
    const uint8_t* p = prow;
    for (int j = 0; j < numCols; j++) {
      luma[i * numCols + j] = (float)(*p);
      p += colStride;
    }
    prow += rowStride;
  }
}

// ----------------------------------------------------------------
void decimateFloat(
    const float* in, // matrix as in_num_rows x in_num_cols in
                     // row-major order
    int inNumRows,
    int inNumCols,
    float* out, // matrix as out_num_rows x out_num_cols in
                // row-major order
    int outNumRows,
    int outNumCols) {
  // target centers not corners:
  for (int outi = 0; outi < outNumRows; outi++) {
    int ini = (int)(((outi + 0.5) * inNumRows) / outNumRows);
    for (int outj = 0; outj < outNumCols; outj++) {
      int inj = (int)(((outj + 0.5) * inNumCols) / outNumCols);
      out[outi * outNumCols + outj] = in[ini * inNumCols + inj];
    }
  }
}

// ----------------------------------------------------------------
void scaleFloatLuma(
    float* fullBuffer1, // matrix as num_rows x num_cols in row-major order
    float* fullBuffer2, // matrix as num_rows x num_cols in row-major order
    int oldNumRows,
    int oldNumCols,
    int numJaroszXYPasses,
    float* scaledLuma, // matrix as num_rows x num_cols in row-major order
    int newNumRows,
    int newNumCols) {
  // Downsample (blur and decimate)
  int windowSizeAlongRows =
      computeJaroszFilterWindowSize(oldNumCols, newNumCols);
  int windowSizeAlongCols =
      computeJaroszFilterWindowSize(oldNumRows, newNumRows);

  jaroszFilterFloat(
      fullBuffer1,
      fullBuffer2,
      oldNumRows,
      oldNumCols,
      windowSizeAlongRows,
      windowSizeAlongCols,
      numJaroszXYPasses);

  decimateFloat(
      fullBuffer1, oldNumRows, oldNumCols, scaledLuma, newNumRows, newNumCols);
}

// ----------------------------------------------------------------
void scaleFloatRGB(
    float* fullBufferR1, // matrix as num_rows x num_cols in row-major order
    float* fullBufferG1, // matrix as num_rows x num_cols in row-major order
    float* fullBufferB1, // matrix as num_rows x num_cols in row-major order
    float* fullBufferR2, // matrix as num_rows x num_cols in row-major order
    float* fullBufferG2, // matrix as num_rows x num_cols in row-major order
    float* fullBufferB2, // matrix as num_rows x num_cols in row-major order
    int oldNumRows,
    int oldNumCols,
    int numJaroszXYPasses,
    float* scaledR, // matrix as num_rows x num_cols in row-major order
    float* scaledG, // matrix as num_rows x num_cols in row-major order
    float* scaledB, // matrix as num_rows x num_cols in row-major order
    int newNumRows,
    int newNumCols) {
  if (newNumRows == oldNumRows && newNumCols == oldNumCols) {
    // E.g. for video-frame processing when we've already used ffmpeg
    // to downsample for us.
    int n = oldNumRows * oldNumCols;
    for (int i = 0; i < n; i++) {
      scaledR[i] = fullBufferR1[i];
      scaledG[i] = fullBufferG1[i];
      scaledB[i] = fullBufferB1[i];
    }
  } else {
    // Downsample (blur and decimate)
    int windowSizeAlongRows =
        computeJaroszFilterWindowSize(oldNumCols, newNumCols);
    int windowSizeAlongCols =
        computeJaroszFilterWindowSize(oldNumRows, newNumRows);

    jaroszFilterFloat(
        fullBufferR1,
        fullBufferR2,
        oldNumRows,
        oldNumCols,
        windowSizeAlongRows,
        windowSizeAlongCols,
        numJaroszXYPasses);

    jaroszFilterFloat(
        fullBufferG1,
        fullBufferG2,
        oldNumRows,
        oldNumCols,
        windowSizeAlongRows,
        windowSizeAlongCols,
        numJaroszXYPasses);

    jaroszFilterFloat(
        fullBufferB1,
        fullBufferB2,
        oldNumRows,
        oldNumCols,
        windowSizeAlongRows,
        windowSizeAlongCols,
        numJaroszXYPasses);

    decimateFloat(
        fullBufferR1, oldNumRows, oldNumCols, scaledR, newNumRows, newNumCols);
    decimateFloat(
        fullBufferG1, oldNumRows, oldNumCols, scaledG, newNumRows, newNumCols);
    decimateFloat(
        fullBufferB1, oldNumRows, oldNumCols, scaledB, newNumRows, newNumCols);
  }
}

// ================================================================
// Round up. See comments at top of file for details.
//
// Since PDQ uses 64x64 blocks, 1/64th of the image height/width respectively
// is a full block. But since we use two passes, we want half that window size
// per pass. Example: 1024x1024 full-resolution input. PDQ downsamples to
// 64x64.  Each 16x16 block of the input produces a single downsample pixel.
// X,Y passes with window size 8 (= 1024/128) average pixels with 8x8
// neighbors. The second X,Y pair of 1D box-filter passes accumulate data from
// all 16x16.
//
// Generalizing beyond PDQ's 64x64 downsample to MxN, the desired value is 2M
// or 2N.
int computeJaroszFilterWindowSize(int oldDimension, int newDimension) {
  return (oldDimension + 2 * newDimension - 1) / (2 * newDimension);
}

// ----------------------------------------------------------------
void jaroszFilterFloat(
    float* buffer1, // matrix as num_rows x num_cols in
                    // row-major order
    float* buffer2, // matrix as num_rows x num_cols in
                    // row-major order
    int numRows,
    int numCols,
    int windowSizeAlongRows,
    int windowSizeAlongCols,
    int nreps) {
  for (int i = 0; i < nreps; i++) {
    boxAlongRowsFloat(buffer1, buffer2, numRows, numCols, windowSizeAlongRows);
    boxAlongColsFloat(buffer2, buffer1, numRows, numCols, windowSizeAlongCols);
  }
}

// ----------------------------------------------------------------
// 7 and 4
//
//    0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1
//    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
//
//    .                                PHASE 1: ONLY ADD, NO WRITE, NO SUBTRACT
//    . .
//    . . .
//
//  0 * . . .                          PHASE 2: ADD, WRITE, WITH NO SUBTRACTS
//  1 . * . . .
//  2 . . * . . .
//  3 . . . * . . .
//
//  4   . . . * . . .                  PHASE 3: WRITES WITH ADD & SUBTRACT
//  5     . . . * . . .
//  6       . . . * . . .
//  7         . . . * . . .
//  8           . . . * . . .
//  9             . . . * . . .
// 10               . . . * . . .
// 11                 . . . * . . .
// 12                   . . . * . . .
//
// 13                     . . . * . .  PHASE 4: FINAL WRITES WITH NO ADDS
// 14                       . . . * .
// 15                         . . . *
//
//         = 0                                     =  0   PHASE 1
//         = 0+1                                   =  1
//         = 0+1+2                                 =  3
//
// out[ 0] = 0+1+2+3                               =  6   PHASE 2
// out[ 1] = 0+1+2+3+4                             = 10
// out[ 2] = 0+1+2+3+4+5                           = 15
// out[ 3] = 0+1+2+3+4+5+6                         = 21
//
// out[ 4] =   1+2+3+4+5+6+7                       = 28   PHASE 3
// out[ 5] =     2+3+4+5+6+7+8                     = 35
// out[ 6] =       3+4+5+6+7+8+9                   = 42
// out[ 7] =         4+5+6+7+8+9+10                = 49
// out[ 8] =           5+6+7+8+9+10+11             = 56
// out[ 9] =             6+7+8+9+10+11+12          = 63
// out[10] =               7+8+9+10+11+12+13       = 70
// out[11] =                 8+9+10+11+12+13+14    = 77
// out[12] =                   9+10+11+12+13+14+15 = 84
//
// out[13] =                     10+11+12+13+14+15 = 75  PHASE 4
// out[14] =                        11+12+13+14+15 = 65
// out[15] =                           12+13+14+15 = 54
// ----------------------------------------------------------------

// ----------------------------------------------------------------
// 8 and 5
//
//    0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1
//    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
//
//    .                                PHASE 1: ONLY ADD, NO WRITE, NO SUBTRACT
//    . .
//    . . .
//    . . . .
//
//  0 * . . . .                        PHASE 2: ADD, WRITE, WITH NO SUBTRACTS
//  1 . * . . . .
//  2 . . * . . . .
//  3 . . . * . . . .
//
//  4   . . . * . . . .                PHASE 3: WRITES WITH ADD & SUBTRACT
//  5     . . . * . . . .
//  6       . . . * . . . .
//  7         . . . * . . . .
//  8           . . . * . . . .
//  9             . . . * . . . .
// 10               . . . * . . . .
// 11                 . . . * . . . .
//
// 12                   . . . * . . .  PHASE 4: FINAL WRITES WITH NO ADDS
// 13                     . . . * . .
// 14                       . . . * .
// 15                         . . . *
//
//         = 0                                     =  0   PHASE 1
//         = 0+1                                   =  1
//         = 0+1+2                                 =  3
//         = 0+1+2+3                               =  6
//
// out[ 0] = 0+1+2+3+4                             = 10
// out[ 1] = 0+1+2+3+4+5                           = 15
// out[ 2] = 0+1+2+3+4+5+6                         = 21
// out[ 3] = 0+1+2+3+4+5+6+7                       = 28
//
// out[ 4] =   1+2+3+4+5+6+7+8                     = 36   PHASE 3
// out[ 5] =     2+3+4+5+6+7+8+9                   = 44
// out[ 6] =       3+4+5+6+7+8+9+10                = 52
// out[ 7] =         4+5+6+7+8+9+10+11             = 60
// out[ 8] =           5+6+7+8+9+10+11+12          = 68
// out[ 9] =             6+7+8+9+10+11+12+13       = 76
// out[10] =               7+8+9+10+11+12+13+14    = 84
// out[11] =                 8+9+10+11+12+13+14+15 = 92
//
// out[12] =                   9+10+11+12+13+14+15 = 84  PHASE 4
// out[13] =                     10+11+12+13+14+15 = 75  PHASE 4
// out[14] =                        11+12+13+14+15 = 65
// out[15] =                           12+13+14+15 = 54
// ----------------------------------------------------------------

void box1DFloat(
    const float* invec,
    float* outvec,
    int vector_length,
    int stride,
    int full_window_size) {
  int half_window_size = (full_window_size + 2) / 2; // 7->4, 8->5

  int phase_1_nreps = half_window_size - 1;
  int phase_2_nreps = full_window_size - half_window_size + 1;
  int phase_3_nreps = vector_length - full_window_size;
  int phase_4_nreps = half_window_size - 1;

  int li = 0; // Index of left edge of read window, for subtracts
  int ri = 0; // Index of right edge of read windows, for adds
  int oi = 0; // Index into output vector

  float sum = 0.0;
  int current_window_size = 0;

  // PHASE 1: ACCUMULATE FIRST SUM NO WRITES
  for (int i = 0; i < phase_1_nreps; i++) {
    sum += invec[ri];
    current_window_size++;
    ri += stride;
  }

  // PHASE 2: INITIAL WRITES WITH SMALL WINDOW
  for (int i = 0; i < phase_2_nreps; i++) {
    sum += invec[ri];
    current_window_size++;
    outvec[oi] = sum / current_window_size;
    ri += stride;
    oi += stride;
  }

  // PHASE 3: WRITES WITH FULL WINDOW
  for (int i = 0; i < phase_3_nreps; i++) {
    sum += invec[ri];
    sum -= invec[li];
    outvec[oi] = sum / current_window_size;
    li += stride;
    ri += stride;
    oi += stride;
  }

  // PHASE 4: FINAL WRITES WITH SMALL WINDOW
  for (int i = 0; i < phase_4_nreps; i++) {
    sum -= invec[li];
    current_window_size--;
    outvec[oi] = sum / current_window_size;
    li += stride;
    oi += stride;
  }
}

// ----------------------------------------------------------------
void boxAlongRowsFloat(
    const float* in, // matrix as num_rows x num_cols in
                     // row-major order
    float* out, // matrix as num_rows x num_cols in row-major
                // order
    int numRows,
    int numCols,
    int window_size) {
  for (int i = 0; i < numRows; i++) {
    box1DFloat(&in[i * numCols], &out[i * numCols], numCols, 1, window_size);
  }
}

// ----------------------------------------------------------------
void boxAlongColsFloat(
    const float* in, // matrix as num_rows x num_cols in
                     // row-major order
    float* out, // matrix as num_rows x num_cols in row-major
                // order
    int numRows,
    int numCols,
    int window_size) {
  for (int j = 0; j < numCols; j++) {
    box1DFloat(&in[j], &out[j], numRows, numCols, window_size);
  }
}

} // namespace downscaling
} // namespace pdq
} // namespace facebook
