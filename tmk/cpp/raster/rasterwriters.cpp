// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// These read stored, possibly rotated RGB frame rasters (one per video frame)
// and unrotate them to their original orientation.
// ================================================================

#include <tmk/cpp/raster/rasterwriters.h>

namespace facebook {
namespace tmk {
namespace raster {

// ----------------------------------------------------------------
unsigned char* AbstractRasterWriter::getPointerToStorageTriple(
    unsigned char* raster,
    int i,
    int j) {
  return &raster[3 * ((i * storageFrameWidth_) + j)];
}

// ----------------------------------------------------------------
size_t NoTransformRasterWriter::writeRGBTriples(
    unsigned char* raster,
    FILE* outputFp) {
  return fwrite(raster, 3, storageFrameWidth_ * storageFrameHeight_, outputFp);
}

// ----------------------------------------------------------------
// Frames were rotated counterclockwise 90 degrees from acquisition to storage.
// Treetops point to the left in the raw storage.  Frames should be rotated
// clockwise 90 degrees from storage to display.
//
// Example: storage has height 20 and width 30.
// Points A,B,C,D are labeled with their (row,column) indices.
//
//   (0,0) B       (0,29) C
//   +-------------+         STORAGE
//   |   <<<   |   |
//   | <<<<<###|   |
//   |  <<<    |   |
//   +-------------+
//   (0,19) A      (29,19) D
//
//   (0,0) A   (0,19) B
//   +---------+             OUTPUT
//   |    ^    |
//   |  ^ ^    |
//   |  ^ ^ ^  |
//   |  ^ ^ ^  |
//   |    ^ ^  |
//   |    #    |
//   |    #    |
//   | ------- |
//   +---------+
//   (29,0) D  (29,19) C

// ----------------------------------------------------------------
size_t RotateCW90RasterWriter::writeRGBTriples(
    unsigned char* raster,
    FILE* outputFp) {
  size_t rc = 0;
  for (int display_i = 0; display_i < storageFrameWidth_; display_i++) {
    for (int display_j = 0; display_j < storageFrameHeight_; display_j++) {
      int storage_i = storageFrameHeight_ - 1 - display_j;
      int storage_j = display_i;
      unsigned char* ptriple =
          getPointerToStorageTriple(raster, storage_i, storage_j);
      size_t rc1 = fwrite(ptriple, 3, 1, outputFp);
      if (rc1 != 1) {
        break;
      }
      rc += rc1;
    }
  }
  return rc;
}

// ----------------------------------------------------------------
// Frames were rotated clockwise 90 degrees from acquisition to storage.
// Treetops point to the right in the raw storage.  Frames should be rotated
// counterclockwise 90 degrees from storage to display.
//
// Example: storage has height 20 and width 30.
// Points A,B,C,D are labeled with their (row,column) indices.
//
//   (0,0) D       (0,29) A
//   +-------------+         STORAGE
//   |  |     >>>  |
//   |  |####>>>>> |
//   |  |    >>>   |
//   +-------------+
//   (0,19) C      (29,19) B
//
//   (0,0) A   (0,19) B
//   +---------+             OUTPUT
//   |    ^    |
//   |  ^ ^    |
//   |  ^ ^ ^  |
//   |  ^ ^ ^  |
//   |    ^ ^  |
//   |    #    |
//   |    #    |
//   | ------- |
//   +---------+
//   (29,0) D  (29,19) C

size_t RotateCCW90RasterWriter::writeRGBTriples(
    unsigned char* raster,
    FILE* outputFp) {
  size_t rc = 0;
  for (int display_i = 0; display_i < storageFrameWidth_; display_i++) {
    for (int display_j = 0; display_j < storageFrameHeight_; display_j++) {
      int storage_i = display_j;
      int storage_j = storageFrameWidth_ - 1 - display_i;
      unsigned char* ptriple =
          getPointerToStorageTriple(raster, storage_i, storage_j);
      size_t rc1 = fwrite(ptriple, 3, 1, outputFp);
      if (rc1 != 1) {
        break;
      }
      rc += rc1;
    }
  }
  return rc;
}

// ----------------------------------------------------------------
// Frames were rotated 180 degrees from acquisition to storage.
// Treetops point downward in the raw storage.
// Frames should be rotated 180 degrees from storage to display.
//
// Example: storage has height 30 and width 20.
// Points A,B,C,D are labeled with their (row,column) indices.

//   (0,0) C   (0,19) D
//   +---------+             OUTPUT
//   | ------- |
//   |    #    |
//   |    #    |
//   |  v v    |
//   |  v # v  |
//   |  v v v  |
//   |    v v  |
//   |    v    |
//   +---------+
//   (29,0) B  (29,19) A

//   (0,0) A   (0,19) B
//   +---------+             OUTPUT
//   |    ^    |
//   |  ^ ^    |
//   |  ^ ^ ^  |
//   |  ^ ^ ^  |
//   |    ^ ^  |
//   |    #    |
//   |    #    |
//   | ------- |
//   +---------+
//   (29,0) D  (29,19) C

size_t Rotate180RasterWriter::writeRGBTriples(
    unsigned char* raster,
    FILE* outputFp) {
  size_t rc = 0;
  for (int display_i = 0; display_i < storageFrameHeight_; display_i++) {
    for (int display_j = 0; display_j < storageFrameWidth_; display_j++) {
      int storage_i = storageFrameHeight_ - 1 - display_i;
      int storage_j = storageFrameWidth_ - 1 - display_j;
      unsigned char* ptriple =
          getPointerToStorageTriple(raster, storage_i, storage_j);
      size_t rc1 = fwrite(ptriple, 3, 1, outputFp);
      if (rc1 != 1) {
        break;
      }
      rc += rc1;
    }
  }
  return rc;
}

// ----------------------------------------------------------------
AbstractRasterWriter* RasterWriterFactory::createFrameWriter(
    RasterTransformation transformation,
    int storageFrameHeight,
    int storageFrameWidth) {
  AbstractRasterWriter* pwriter = nullptr;
  switch (transformation) {
    case RasterTransformation::NEEDS_NO_TRANSFORMATION:
      pwriter =
          new NoTransformRasterWriter(storageFrameHeight, storageFrameWidth);
      break;
    // Storage is CCW 90 degrees from display. Undo
    // by rotating CW 90 degrees.
    case RasterTransformation::NEEDS_ROTATE_CW_90:
      pwriter =
          new RotateCW90RasterWriter(storageFrameHeight, storageFrameWidth);
      break;
    // Storage is CW 90 degrees from display. Undo
    // by rotating CCW 90 degrees.
    case RasterTransformation::NEEDS_ROTATE_CCW_90:
      pwriter =
          new RotateCCW90RasterWriter(storageFrameHeight, storageFrameWidth);
      break;
    case RasterTransformation::NEEDS_ROTATE_180:
      pwriter =
          new Rotate180RasterWriter(storageFrameHeight, storageFrameWidth);
      break;
    default:
      break;
  }

  return pwriter;
}

} // namespace raster
} // namespace tmk
} // namespace facebook
