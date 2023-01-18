// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef SCALING_H
#define SCALING_H

// ================================================================
// Wojciech Jarosz 'Fast Image Convolutions' ACM SIGGRAPH 2001:
// X,Y     passes of 1-D box filters produces a 2D box filter;
// X,Y,X,Y passes of 1-D box filters produces a 2D tent filter.
//
// Workspace buffers are exposed as arguments in the API, rather than being
// allocated and freed inside of routines, in order to facilitate efficient
// video-frame processing. For video frames there is a large number of 'images'
// each with the same dimensions so we may as well allocate workspaces once at
// the start of the video, re-use them on each frame, and then free them at the
// end.
// ================================================================

namespace facebook {
namespace pdq {
namespace downscaling {

using uint8_t = unsigned char;

// ----------------------------------------------------------------
// Matrix of RGB-triple unsigned chars -> matrix of floating-point luminance
void fillFloatLumaFromRGB(
    const uint8_t* pRbase,
    const uint8_t* pGbase,
    const uint8_t* pBbase,
    int numRows, // Number of RGB triples per row
    int numCols, // Number of RGB triples per column
    int rowStride, // Difference in bytes from row 0 to row 1 (e.g. 3 * numCols)
    int colStride, // Difference in bytes from col 0 to col 1 (e.g. 3)
    float* luma // matrix as num_rows x num_cols in row-major order
);

// Matrix of greyscale unsigned char -> matrix of floating-point luminance
void fillFloatLumaFromGrey(
    const uint8_t* pbase,
    int numRows,
    int numCols,
    int rowStride,
    int colStride,
    float* luma // matrix as num_rows x num_cols in row-major order
);

// ----------------------------------------------------------------
// Matrix of RGB-triple unsigned chars -> matrices of floating-point R/G/B
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
);

// Matrix of greyscale unsigned char -> matrices of floating-point R/G/B
// (R/G/B at same (i,j) have the same grey value).
void fillFloatRGBFromGrey(
    const uint8_t* pbase,
    int numRows,
    int numCols,
    int rowStride,
    int colStride,
    float* pFloatR, // matrix as num_rows x num_cols in row-major order
    float* pFloatG, // matrix as num_rows x num_cols in row-major order
    float* pFloatB // matrix as num_rows x num_cols in row-major order
);

// ----------------------------------------------------------------
void scaleFloatLuma(
    float* fullBuffer1, // matrix as num_rows x num_cols in row-major order
    float* fullBuffer2, // matrix as num_rows x num_cols in row-major order
    int oldNumRows,
    int oldNumCols,
    int numJaroszXYPasses,
    float* scaledLuma, // matrix as num_rows x num_cols in row-major order
    int newNumRows,
    int newNumCols);

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
    int newNumCols);

// ----------------------------------------------------------------
// These are all nominally private to the downsampler. However they are
// exposed for testing/documentation purposes.

// Given full-resolution input-image height/width, respectively, find the window
// size for a single 1D pass.
int computeJaroszFilterWindowSize(int oldDimension, int newDimension);

void jaroszFilterFloat(
    float* buffer1,
    float* buffer2,
    int numRows,
    int numCols,
    int windowSizeAlongRows,
    int windowSizeAlongCols,
    int nreps);

// matrices as num_rows x num_cols in row-major order
void boxAlongRowsFloat(
    const float* in, float* out, int numRows, int numCols, int windowSize);
void boxAlongColsFloat(
    const float* in, float* out, int numRows, int numCols, int windowSize);

void box1DFloat(
    const float* invec,
    float* outvec,
    int vector_length,
    int stride,
    int full_window_size);

void decimateFloat(
    const float* in, // matrix as in_num_rows x in_num_cols in row-major order
    int inNumRows,
    int inNumCols,
    float* out, // matrix as out_num_rows x out_num_cols in row-major order
    int outNumRows,
    int outNumCols);

} // namespace downscaling
} // namespace pdq
} // namespace facebook

#endif // SCALING_H
