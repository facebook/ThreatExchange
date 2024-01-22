// Copyright (c) Meta Platforms, Inc. and affiliates.
#include "pdqhashing.h"
#include "torben.h"
#include <math.h>

//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Wojciech Jarosz 'Fast Image Convolutions' ACM SIGGRAPH 2001:
// X,Y,X,Y passes of 1-D box filters produces a 2D tent filter.
static const int PDQ_NUM_JAROSZ_XY_PASSES = 2;
// Since PDQ uses 64x64 blocks, 1/64th of the image height/width respectively is
// a full block. But since we use two passes, we want half that window size per
// pass. Example: 1024x1024 full-resolution input. PDQ downsamples to 64x64.
// Each 16x16 block of the input produces a single downsample pixel.  X,Y passes
// with window size 8 (= 1024/128) average pixels with 8x8 neighbors. The second
// X,Y pair of 1D box-filter passes accumulate data from all 16x16.
static const int PDQ_JAROSZ_WINDOW_SIZE_DIVISOR = 128;

// Minimum size tested.
static const int MIN_HASHABLE_DIM = 5;

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
      float yval =
        luma_from_R_coeff * (*pR) +
        luma_from_G_coeff * (*pG) +
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
void decimateFloat(
  float* A, // numRows x numCols, row-major
  int numRows,
  int numCols,
  float B[64][64]
) {
  // target centers not corners:
  for (int i = 0; i < 64; i++) {
    int ini = (int)(((i + 0.5) * numRows) / 64);
    for (int j = 0; j < 64; j++) {
      int inj = (int)(((j + 0.5) * numCols) / 64);
      B[i][j] = A[ini * numCols + inj];
    }
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
  Hash256* phash,
  int* pquality
) {
  if (numRows < MIN_HASHABLE_DIM || numCols < MIN_HASHABLE_DIM) {
    Hash256Clear(phash);
    *pquality = 0;
    return;
  }

  // Downsample (blur and decimate)
  int windowSizeAlongRows = computeJaroszFilterWindowSize(numCols);
  int windowSizeAlongCols = computeJaroszFilterWindowSize(numRows);

  jaroszFilterFloat(
    fullBuffer1,
    fullBuffer2,
    numRows,
    numCols,
    windowSizeAlongRows,
    windowSizeAlongCols,
    PDQ_NUM_JAROSZ_XY_PASSES
  );

  decimateFloat(fullBuffer1, numRows, numCols, buffer64x64);

  // Quality metric.  Reuse the 64x64 image-domain downsample
  // since we already have it.
  *pquality = pdqImageDomainQualityMetric(buffer64x64);

  // 2D DCT
  dct64To16(buffer64x64, buffer16x64, buffer16x16);

  // Output bits
  pdqBuffer16x16ToBits(buffer16x16, phash);
}

// ----------------------------------------------------------------
bool_t pdqDihedralHash256esFromFloatLuma(
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
  int* pquality
) {
  if (numRows < MIN_HASHABLE_DIM || numCols < MIN_HASHABLE_DIM) {
    if (hashptrOriginal != NULL) {
      Hash256Clear(hashptrOriginal);
    }
    if (hashptrRotate90 != NULL) {
      Hash256Clear(hashptrRotate90);
    }
    if (hashptrRotate180 != NULL) {
      Hash256Clear(hashptrRotate180);
    }
    if (hashptrRotate270 != NULL) {
      Hash256Clear(hashptrRotate270);
    }
    if (hashptrFlipX != NULL) {
      Hash256Clear(hashptrFlipX);
    }
    if (hashptrFlipY != NULL) {
      Hash256Clear(hashptrFlipY);
    }
    if (hashptrFlipPlus1 != NULL) {
      Hash256Clear(hashptrFlipPlus1);
    }
    if (hashptrFlipMinus1 != NULL) {
      Hash256Clear(hashptrFlipMinus1);
    }
    *pquality = 0;
    return true;
  }

  // Downsample (blur and decimate)
  int windowSizeAlongRows = computeJaroszFilterWindowSize(numCols);
  int windowSizeAlongCols = computeJaroszFilterWindowSize(numRows);

  jaroszFilterFloat(
    fullBuffer1,
    fullBuffer2,
    numRows,
    numCols,
    windowSizeAlongRows,
    windowSizeAlongCols,
    PDQ_NUM_JAROSZ_XY_PASSES
  );

  decimateFloat(fullBuffer1, numRows, numCols, buffer64x64);

  // Quality metric.  Reuse the 64x64 image-domain downsample
  // since we already have it.
  *pquality = pdqImageDomainQualityMetric(buffer64x64);

  // 2D DCT
  dct64To16(buffer64x64, buffer16x64, buffer16x16);

  //  Output bits
  if (hashptrOriginal != NULL) {
    pdqBuffer16x16ToBits(buffer16x16, hashptrOriginal);
  }
  if (hashptrRotate90 != NULL) {
    dct16OriginalToRotate90(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrRotate90);
  }
  if (hashptrRotate180 != NULL) {
    dct16OriginalToRotate180(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrRotate180);
  }
  if (hashptrRotate270 != NULL) {
    dct16OriginalToRotate270(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrRotate270);
  }
  if (hashptrFlipX != NULL) {
    dct16OriginalToFlipX(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrFlipX);
  }
  if (hashptrFlipY != NULL) {
    dct16OriginalToFlipY(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrFlipY);
  }
  if (hashptrFlipPlus1 != NULL) {
    dct16OriginalToFlipPlus1(buffer16x16, buffer16x16Aux);
    pdqBuffer16x16ToBits(buffer16x16Aux, hashptrFlipPlus1);
  }
  if (hashptrFlipMinus1 != NULL) {
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
      float v = buffer64x64[i+1][j];
      int d = ((u - v) * 100) / 255;
	  // Accumulate absolute value
      gradient_sum += (d < 0) ? -d : d;
    }
  }
  for (int i = 0; i < 64; i++) {
    for (int j = 0; j < 63; j++) {
      float u = buffer64x64[i][j];
      float v = buffer64x64[i][j+1];
      int d = ((u - v) * 100) / 255;
      gradient_sum += (d < 0) ? -d : d;
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

void dct64To16(
  float A[64][64],
  float T[16][64],
  float B[16][16]
) {
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
      float* pd = &D[i*64]; // ith row
      float* pa = &A[0][j];
      float sumk = 0.0;

      for (int k = 0; k < 64; ) {
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
      float* pd = &D[j*64]; // jth row
      float* pt = &T[i][0];
      for (int k = 0; k < 64; ) {
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
        sumk += pt[k] * pd[k]; k++;
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
void dct16OriginalToRotate90(
  float A[16][16],
  float B[16][16]
) {
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

void dct16OriginalToRotate180(
  float A[16][16],
  float B[16][16]
) {
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      if ((i+j) & 1) {
        B[i][j] = -A[i][j];
      } else {
        B[i][j] = A[i][j];
      }
    }
  }
}

void dct16OriginalToRotate270(
  float A[16][16],
  float B[16][16]
) {
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

void dct16OriginalToFlipX(
  float A[16][16],
  float B[16][16]
) {
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

void dct16OriginalToFlipY(
  float A[16][16],
  float B[16][16]
) {
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

void dct16OriginalToFlipPlus1(
  float A[16][16],
  float B[16][16]
) {
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      B[j][i] = A[i][j];
    }
  }
}

void dct16OriginalToFlipMinus1(
  float A[16][16],
  float B[16][16]
) {
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      if ((i+j) & 1) {
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
void pdqBuffer16x16ToBits(
  float dctOutput16x16[16][16],
  Hash256* hashptr
) {

  float dct_median = torben(&dctOutput16x16[0][0], 16*16);

  Hash256Clear(hashptr);
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 16; j++) {
      if (dctOutput16x16[i][j] > dct_median) {
        Hash256SetBit(hashptr, i*16 + j);
      }
    }
  }
}

// ================================================================
// Round up. See comments at top of file for details.
int computeJaroszFilterWindowSize(int dimension) {
  return (dimension + PDQ_JAROSZ_WINDOW_SIZE_DIVISOR - 1)
    / PDQ_JAROSZ_WINDOW_SIZE_DIVISOR;
}

// ----------------------------------------------------------------
void jaroszFilterFloat(
  float* buffer1, // numRows x numCols, row-major
  float* buffer2, // numRows x numCols, row-major
  int numRows,
  int numCols,
  int windowSizeAlongRows,
  int windowSizeAlongCols,
  int nreps
) {
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
  float* invec,
  float* outvec,
  int    vector_length,
  int    stride,
  int    full_window_size
) {
  int half_window_size = (full_window_size+2)/2; // 7->4, 8->5

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

void box1DInt(
  int* invec,
  int* outvec,
  int  vector_length,
  int  stride,
  int  full_window_size
) {
  int half_window_size = (full_window_size+2)/2; // 7->4, 8->5

  int phase_1_nreps = half_window_size - 1;
  int phase_2_nreps = full_window_size - half_window_size + 1;
  int phase_3_nreps = vector_length - full_window_size;
  int phase_4_nreps = half_window_size - 1;

  int li = 0; // Index of left edge of read window, for subtracts
  int ri = 0; // Index of right edge of read windows, for adds
  int oi = 0; // Index into output vector

  int sum = 0;
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
  float* A, // numRows x numCols, row-major
  float* B, // numRows x numCols, row-major
  int numRows,
  int numCols,
  int window_size
) {
  for (int i = 0; i < numRows; i++) {
    box1DFloat(&A[i * numCols], &B[i * numCols], numCols, 1, window_size);
  }
}

// ----------------------------------------------------------------
void boxAlongColsFloat(
  float* A, // numRows x numCols, row-major
  float* B, // numRows x numCols, row-major
  int numRows,
  int numCols,
  int window_size
) {
  for (int j = 0; j < numCols; j++) {
    box1DFloat(&A[j], &B[j], numRows, numCols, window_size);
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
  static bool_t initialized = false;
  static float buffer[16 * 64];
  if (!initialized) {
    const float matrix_scale_factor = sqrt(2.0 / 64.0);
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 64; j++) {
        buffer[i * 64 + j] = matrix_scale_factor *
          cos((M_PI / 2 / 64.0) * (i+1) * (2 * j + 1));
      }
    }
    initialized = true;
  }
  return &buffer[0];
}
