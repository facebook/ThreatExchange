// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef PDQIO_H
#define PDQIO_H

// ================================================================
// CImg-dependent interface for reading files to matrices of RGB triples.
// ================================================================

#include <pdq/cpp/common/pdqhashtypes.h>
#define cimg_display 0
#include "CImg.h"

#include <cstdint>

namespace facebook {
namespace pdq {
namespace hashing {

// Returns matrix as numRows x numCols in row-major order.
// The caller must free the return value.
// xxx check for this.
float* loadFloatLumaFromCImg(
    cimg_library::CImg<uint8_t>& img, int& numRows, int& numCols);

void showDecoderInfo();

bool pdqHash256FromFile(
    const char* filename,
    Hash256& hash,
    int& quality,
    int& imageHeightTimesWidth,
    float& readSeconds,
    float& hashSeconds);

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
    float& hashSeconds);

// Takes matrix as numRows x numCols in row-major order
void floatMatrixToCImg(
    float* matrix, int numRows, int numCols, const char filename[]);

} // namespace hashing
} // namespace pdq
} // namespace facebook

#endif // PDQIO_H
