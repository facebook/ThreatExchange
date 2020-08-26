// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// These allow us to resample videos at a constant rate, be it slower than,
// same as, or faster than the original video's frame rate.
// ================================================================

#include "timeresamplers.h"
#include <stdio.h>
#include <stdlib.h>
#include <memory>
#include <stdexcept>

namespace facebook {
namespace tmk {
namespace raster {

// ----------------------------------------------------------------
int SameRateTimeResampler::numberToEmit() {
  inputFrameNumber_++;
  outputFrameNumber_++;
  return 1; // always emit
}

// ----------------------------------------------------------------
int SlowDownTimeResampler::numberToEmit() {
  double istamp = inputFrameNumber_ * inputSecondsPerFrame_;
  if (istamp >= nextOutputTime_) {
    nextOutputTime_ += outputSecondsPerFrame_;
    inputFrameNumber_++;
    outputFrameNumber_++;
    return 1;
  } else {
    inputFrameNumber_++;
    return 0;
  }
}

// ----------------------------------------------------------------
int SpeedUpTimeResampler::numberToEmit() {
  int retval = 0;
  double ostamp = outputFrameNumber_ * outputSecondsPerFrame_;
  while (ostamp <= nextInputTime_) {
    ostamp += outputSecondsPerFrame_;
    retval++;
  }
  nextInputTime_ += inputSecondsPerFrame_;
  inputFrameNumber_++;
  outputFrameNumber_ += retval;
  return retval;
}

// ----------------------------------------------------------------
std::unique_ptr<AbstractTimeResampler>
TimeResamplerFactory::createTimeResampler(
    double inputFramesPerSecond,
    int outputFramesPerSecond) {
  std::unique_ptr<AbstractTimeResampler> ptimeResampler;
  if (inputFramesPerSecond == outputFramesPerSecond) {
    ptimeResampler = std::make_unique<SameRateTimeResampler>(
        inputFramesPerSecond, outputFramesPerSecond);
  } else if (inputFramesPerSecond > outputFramesPerSecond) {
    ptimeResampler = std::make_unique<SlowDownTimeResampler>(
        inputFramesPerSecond, outputFramesPerSecond);
  } else if (inputFramesPerSecond < outputFramesPerSecond) {
    ptimeResampler = std::make_unique<SpeedUpTimeResampler>(
        inputFramesPerSecond, outputFramesPerSecond);
  } else {
    // NaNs fail all equality/inequality test so that's the only way
    // none of < == > cases would have happened.
    throw std::runtime_error(
        "Apparent NaN value(s): " + std::to_string(inputFramesPerSecond) +
        ", " + std::to_string(outputFramesPerSecond));
  }
  return ptimeResampler;
}

} // namespace raster
} // namespace tmk
} // namespace facebook
