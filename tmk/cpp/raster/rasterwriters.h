// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// These read stored, possibly rotated RGB frame rasters (one per video frame)
// and unrotate them to their original orientation.
// ================================================================

#ifndef RASTERWRITERS_H
#define RASTERWRITERS_H
#include <stdio.h>

namespace facebook {
namespace tmk {
namespace raster {

enum class RasterTransformation {
  NEEDS_NO_TRANSFORMATION,
  NEEDS_ROTATE_CW_90,
  NEEDS_ROTATE_CCW_90,
  NEEDS_ROTATE_180
};

class AbstractRasterWriter {
 protected:
  int storageFrameHeight_;
  int storageFrameWidth_;
  int displayFrameHeight_;
  int displayFrameWidth_;

 public:
  AbstractRasterWriter(int storageFrameHeight, int storageFrameWidth)
      : storageFrameHeight_(storageFrameHeight),
        storageFrameWidth_(storageFrameWidth) {}
  virtual ~AbstractRasterWriter() {}

  // Returns number of triples written
  virtual size_t writeRGBTriples(unsigned char* raster, FILE* outputFp) = 0;
  unsigned char* getPointerToStorageTriple(unsigned char* raster, int i, int j);
  int getDisplayFrameHeight() const {
    return displayFrameHeight_;
  }
  int getDisplayFrameWidth() const {
    return displayFrameWidth_;
  }
};

// ----------------------------------------------------------------
class NoTransformRasterWriter : public AbstractRasterWriter {
 public:
  NoTransformRasterWriter(int storageFrameHeight, int storageFrameWidth)
      : AbstractRasterWriter(storageFrameHeight, storageFrameWidth) {
    displayFrameHeight_ = storageFrameHeight;
    displayFrameWidth_ = storageFrameWidth;
  }
  ~NoTransformRasterWriter() {}
  size_t writeRGBTriples(unsigned char* raster, FILE* outputFp) override;
};

// Frames were rotated counterclockwise 90 degrees from acquisition to storage.
// Treetops point to the left in the raw storage.  Frames should be rotated
// clockwise 90 degrees from storage to display.
class RotateCW90RasterWriter : public AbstractRasterWriter {
 public:
  RotateCW90RasterWriter(int storageFrameHeight, int storageFrameWidth)
      : AbstractRasterWriter(storageFrameHeight, storageFrameWidth) {
    displayFrameHeight_ = storageFrameWidth;
    displayFrameWidth_ = storageFrameHeight;
  }
  ~RotateCW90RasterWriter() {}
  size_t writeRGBTriples(unsigned char* raster, FILE* outputFp) override;
};

// Frames were rotated clockwise 90 degrees from acquisition to storage.
// Treetops point to the right in the raw storage.  Frames should be rotated
// counterclockwise 90 degrees from storage to display.
class RotateCCW90RasterWriter : public AbstractRasterWriter {
 public:
  RotateCCW90RasterWriter(int storageFrameHeight, int storageFrameWidth)
      : AbstractRasterWriter(storageFrameHeight, storageFrameWidth) {
    displayFrameHeight_ = storageFrameWidth;
    displayFrameWidth_ = storageFrameHeight;
  }
  ~RotateCCW90RasterWriter() {}
  size_t writeRGBTriples(unsigned char* raster, FILE* outputFp) override;
};

// Frames were rotated 180 degrees from acquisition to storage.
// Treetops point downward in the raw storage.
// That needs to be undone.
class Rotate180RasterWriter : public AbstractRasterWriter {
 public:
  Rotate180RasterWriter(int storageFrameHeight, int storageFrameWidth)
      : AbstractRasterWriter(storageFrameHeight, storageFrameWidth) {
    displayFrameHeight_ = storageFrameHeight;
    displayFrameWidth_ = storageFrameWidth;
  }
  ~Rotate180RasterWriter() {}
  size_t writeRGBTriples(unsigned char* raster, FILE* outputFp) override;
};

// ----------------------------------------------------------------
class RasterWriterFactory {
 public:
  static AbstractRasterWriter* createFrameWriter(
      RasterTransformation transformation,
      int storageFrameHeight,
      int storageFrameWidth);
};

} // namespace raster
} // namespace tmk
} // namespace facebook

#endif // RASTERWRITERS_H
