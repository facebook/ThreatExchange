// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// These allow us to resample videos at a constant rate, be it slower than,
// same as, or faster than the original video's frame rate.
// ================================================================

#ifndef TIMERESAMPLERS_H
#define TIMERESAMPLERS_H

#include <string>
#include <memory>

namespace facebook {
namespace tmk {
namespace raster {

// ----------------------------------------------------------------
// Why floating-point input frames per second but integer output frames per
// second:
//
// In the wild, absolutely frame rates are not necessarily integers -- 29.98 or
// what have you.  For TMK we resample to a constant rate: Lorenzo Baraldi used
// 15 FPS and that seems like as good a choice as any. Since we are resampling
// to a constant rate we may as well use an integer and avoid ever having the
// possibility of roundoff error throughout the rest of the TMK code downstream
// from this initial raster-manipulation.

class AbstractTimeResampler {
 protected:
  double inputFramesPerSecond_;
  double outputFramesPerSecond_;
  double inputSecondsPerFrame_;
  double outputSecondsPerFrame_;
  int inputFrameNumber_ = 0;
  int outputFrameNumber_ = 0;

 public:
  AbstractTimeResampler(double inputFramesPerSecond, int outputFramesPerSecond)
      : inputFramesPerSecond_(inputFramesPerSecond),
        outputFramesPerSecond_((double)outputFramesPerSecond) {
    inputFramesPerSecond_ = inputFramesPerSecond;
    outputFramesPerSecond_ = (double)outputFramesPerSecond;
    inputSecondsPerFrame_ = 1.0 / inputFramesPerSecond_;
    outputSecondsPerFrame_ = 1.0 / outputFramesPerSecond_;
    if (inputFramesPerSecond <= 0.0 || outputFramesPerSecond <= 0.0) {
      throw std::runtime_error(
          "Frame rates must be positive: got " +
          std::to_string(inputFramesPerSecond) + ", " +
          std::to_string(outputFramesPerSecond));
    }
  }

  double inputFrameNumberToTimestamp(int inputFrameNumber) const {
    return inputFrameNumber * inputSecondsPerFrame_;
  }

  double outputFrameNumberToTimestamp(int outputFrameNumber) const {
    return outputFrameNumber * outputSecondsPerFrame_;
  }

  virtual ~AbstractTimeResampler() {}

  // Returns number of triples written
  virtual int numberToEmit() = 0;
};

// ----------------------------------------------------------------
class SameRateTimeResampler : public AbstractTimeResampler {
 public:
  SameRateTimeResampler(double inputFramesPerSecond, int outputFramesPerSecond)
      : AbstractTimeResampler(inputFramesPerSecond, outputFramesPerSecond) {}

  int numberToEmit() override;
};

class SlowDownTimeResampler : public AbstractTimeResampler {
 private:
  double nextOutputTime_ = 0.0;

 public:
  SlowDownTimeResampler(double inputFramesPerSecond, int outputFramesPerSecond)
      : AbstractTimeResampler(inputFramesPerSecond, outputFramesPerSecond) {}

  int numberToEmit() override;
};

class SpeedUpTimeResampler : public AbstractTimeResampler {
 private:
  double nextInputTime_ = 0.0;

 public:
  SpeedUpTimeResampler(double inputFramesPerSecond, int outputFramesPerSecond)
      : AbstractTimeResampler(inputFramesPerSecond, outputFramesPerSecond) {}

  int numberToEmit() override;
};

// ----------------------------------------------------------------
class TimeResamplerFactory {
 public:
  static std::unique_ptr<AbstractTimeResampler> createTimeResampler(
      double inputFramesPerSecond,
      int outputFramesPerSecond);
};

} // namespace raster
} // namespace tmk
} // namespace facebook

#endif // TIMERESAMPLERS_H
