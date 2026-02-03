// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef PDQHASHING_H
#define PDQHASHING_H

// ================================================================
// PDQ algorithm description:
// https://github.com/facebookexternal/ThreatExchange-PDQ/blob/main/pdqhash-2017-10-09.pdf
// ================================================================

#include <pdq/cpp/common/pdqhashtypes.h>

#include <cstdint>

namespace facebook {
namespace pdq {
namespace hashing {

// ----------------------------------------------------------------
void fillFloatLumaFromRGB(
    uint8_t* pRbase,
    uint8_t* pGbase,
    uint8_t* pBbase,
    int numRows,
    int numCols,
    int rowStride,
    int colStride,
    float* luma // output, numRows x numCols, row-major
);

void fillFloatLumaFromGrey(
    uint8_t* pbase,
    int numRows,
    int numCols,
    int rowStride,
    int colStride,
    float* luma // output, numRows x numCols, row-major
);

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
    int& quality);

void pdqFloat256FromFloatLuma(
    float* fullBuffer1, // numRows x numCols, row-major
    float* fullBuffer2, // numRows x numCols, row-major
    int numRows,
    int numCols,
    float buffer64x64[64][64],
    float buffer16x64[16][64],
    float output_buffer16x16[16][16],
    int& quality);

// Naming conventions:
// * Rotate 90: counterclockwise 90 degrees
// * Rotate 180: 180 degrees
// * Rotate 270: counterclockwise 270 degrees (i.e. clockwise 90 degrees)
// * FlipX: Left is left and right is right but top and bottom change places
// * FlipY: Top is top and bottom is bottom but left and right change places
//   (mirror image)
// * FlipPlus1: Upper left and lower right stay put; lower left and upper right
//   exchange places
// * FlipMinus: Upper right and lower left stay put; upper left and lower right
//   exchange places
//
// Pointer semantics:
// * Pass nullptr for any variants you do not want to be computed.
// * Pass pointer to hashes to be stuffed with variants you do want computed.
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
    int& quality);

// ----------------------------------------------------------------
// These are all nominally private to the hasher. However they are
// exposed for testing/documentation purposes.

// Given full-resolution input-image height/width, respectively, find the window
// size for a single 1D pass.
int computeJaroszFilterWindowSize(int dimension);

void jaroszFilterFloat(
    float* fullBuffer1, // numRows x numCols, row-major
    float* fullBuffer2, // numRows x numCols, row-major
    int numRows,
    int numCols,
    int windowSizeAlongRows,
    int windowSizeAlongCols,
    int nreps);

void boxAlongRowsFloat(
    float* in, // numRows x numCols, row-major
    float* out, // numRows x numCols, row-major
    int numRows,
    int numCols,
    int window_size);

void boxAlongColsFloat(
    float* in, // numRows x numCols, row-major
    float* out, // numRows x numCols, row-major
    int numRows,
    int numCols,
    int window_size);

void box1DFloat(
    float* invec,
    float* outvec,
    int vector_length,
    int stride,
    int full_window_size);

void decimateFloat(
    float* in, // inNumRows x inNumCols, row-major
    int inNumRows,
    int inNumCols,
    float out[64][64]);

int pdqImageDomainQualityMetric(float buffer64x64[64][64]);

void dct64To16(
    float buffer64x64[64][64],
    float buffer16x64[16][64],
    float buffer16x16[16][16]);

// All are 16x16
void dct16OriginalToRotate90(float inm[16][16], float outm[16][16]);
void dct16OriginalToRotate180(float inm[16][16], float outm[16][16]);
void dct16OriginalToRotate270(float inm[16][16], float outm[16][16]);
void dct16OriginalToFlipX(float inm[16][16], float outm[16][16]);
void dct16OriginalToFlipY(float inm[16][16], float outm[16][16]);
void dct16OriginalToFlipPlus1(float inm[16][16], float outm[16][16]);
void dct16OriginalToFlipMinus1(float inm[16][16], float outm[16][16]);

void pdqBuffer16x16ToBits(float dctOutput16x16[16][16], Hash256* hashptr);

} // namespace hashing
} // namespace pdq
} // namespace facebook

#endif // PDQHASHING_H
