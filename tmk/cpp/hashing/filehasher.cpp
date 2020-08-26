// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/hashing/bufferhashers.h>
#include <tmk/cpp/io/tmkio.h>

#include <stdio.h>
#include <memory>

using namespace std;

namespace facebook {
namespace tmk {
namespace hashing {

bool hashVideo(
    int downsampleFrameDimension,
    std::string ffmpegGeneratorCommand,
    io::TMKFramewiseAlgorithm tmkFramewiseAlgorithm,
    int resampleFramesPerSecond,
    facebook::tmk::algo::TMKFeatureVectors& tmkFeatureVectors,
    bool verbose,
    const char* argv0) {
  if (verbose) {
    fprintf(stderr, "%s\n", ffmpegGeneratorCommand.c_str());
  }

  FILE* inputFp = popen(ffmpegGeneratorCommand.c_str(), "r");
  if (inputFp == nullptr) {
    fprintf(stderr, "%s: ffmpeg to generate video stream failed\n", argv0);
    return false;
  }

  // ----------------------------------------------------------------
  std::unique_ptr<tmk::hashing::AbstractFrameBufferHasher> phasher =
      tmk::hashing::FrameBufferHasherFactory::createFrameHasher(
          tmkFramewiseAlgorithm,
          downsampleFrameDimension,
          downsampleFrameDimension);

  if (phasher == nullptr) {
    fprintf(stderr, "Error: Phasher is null");
    return false;
  }

  int frameFeatureDimension = phasher->getFeatureDimension();

  // ----------------------------------------------------------------
  // Allocate this and re-use it over frames, rather than allocating/freeing
  // on each frame.
  std::unique_ptr<uint8_t[]> rawFrameBuffer(
      new uint8_t[downsampleFrameDimension * downsampleFrameDimension * 3]);
  std::vector<float> feature(frameFeatureDimension);

  std::vector<int> periods =
      facebook::tmk::algo::TMKFeatureVectors::makePoullotPeriods();

  std::vector<float> fourierCoefficients =
      facebook::tmk::algo::TMKFeatureVectors::makePoullotFourierCoefficients();

  tmkFeatureVectors = facebook::tmk::algo::TMKFeatureVectors(
      tmkFramewiseAlgorithm,
      resampleFramesPerSecond,
      periods,
      fourierCoefficients,
      frameFeatureDimension);
  try {
    bool eof = false;
    while (!feof(inputFp)) {
      bool read_rc = facebook::tmk::io::readRGBTriples(
          rawFrameBuffer.get(),
          downsampleFrameDimension,
          downsampleFrameDimension,
          inputFp,
          eof);
      if (eof) {
        break;
      }
      if (!read_rc) {
        perror("fread");
        fprintf(
            stderr,
            "%s: failed to read frame buffer %d.\n",
            argv0,
            tmkFeatureVectors.getFrameFeatureCount());
        return false;
      }

      if (!phasher->hashFrame(rawFrameBuffer.get(), feature)) {
        fprintf(
            stderr,
            "%s: failed to hash frame buffer %d.\n",
            argv0,
            tmkFeatureVectors.getFrameFeatureCount());
        return false;
      }

      tmkFeatureVectors.ingestFrameFeature(
          feature, tmkFeatureVectors.getFrameFeatureCount());
    }
  } catch (const exception& e) {
    fprintf(stderr, "%s: failed to download and hash video.\n", argv0);
    fprintf(stderr, "%s\n", e.what());
    return false;
  }
  tmkFeatureVectors.finishFrameFeatureIngest();

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // This includes failure to exec the subordinate process.
  int pclose_rc = pclose(inputFp);
  if (pclose_rc != 0) {
    fprintf(stderr, "%s: ffmpeg pclose return code %d.\n", argv0, pclose_rc);
    return false;
  }

  return true;
}

bool hashEverstoreVideoFile(
    const std::string& inputEverstoreHandle,
    io::TMKFramewiseAlgorithm tmkFramewiseAlgorithm,
    const std::string& ffmpegPath,
    const std::string& everstorePath,
    int resampleFramesPerSecond,
    facebook::tmk::algo::TMKFeatureVectors& tmkFeatureVectors,
    bool verbose,
    const char* argv0) {
  int downsampleFrameDimension =
      tmk::hashing::FrameBufferHasherFactory::getFrameHasherDownscaleDimension(
          tmkFramewiseAlgorithm);

  std::string everstoreCommand =
      everstorePath + " --input_everstore_handle=" + inputEverstoreHandle;

  std::string ffmpegGeneratorCommand = everstoreCommand + " | " + ffmpegPath +
      " -f mp4 " + " -i " + "pipe: " + " -s " +
      std::to_string(downsampleFrameDimension) + ":" +
      std::to_string(downsampleFrameDimension) +
      " -an -f rawvideo -c:v rawvideo -pix_fmt rgb24 -r " +
      std::to_string(resampleFramesPerSecond) + " pipe:1";
  return hashVideo(
      downsampleFrameDimension,
      ffmpegGeneratorCommand,
      tmkFramewiseAlgorithm,
      resampleFramesPerSecond,
      tmkFeatureVectors,
      verbose,
      argv0);
}

bool hashVideoFile(
    const std::string& inputVideoFileName,
    io::TMKFramewiseAlgorithm tmkFramewiseAlgorithm,
    const std::string& ffmpegPath,
    int resampleFramesPerSecond,
    facebook::tmk::algo::TMKFeatureVectors& tmkFeatureVectors,
    bool verbose,
    const char* argv0) {
  int downsampleFrameDimension =
      tmk::hashing::FrameBufferHasherFactory::getFrameHasherDownscaleDimension(
          tmkFramewiseAlgorithm);

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // These are the parameters for the ffmpeg that we will use to created
  // the video stream. We want to use popen so we can build a binary instead
  // of a script to ease the process of adding the executable to a package.
  // It's essential for cross-company hash-sharing that we execute as close
  // to the same code our partners will as possible.
  //
  // This is like:
  //
  //   output_width=64
  //   output_height=64
  //   output_fps=15
  //   ffmpeg -i "$1" \
  //     -s ${output_width}:${output_height} -an -f rawvideo -c:v rawvideo \
  //     -pix_fmt rgb24 -r $output_fps pipe:1

  std::string command = ffmpegPath + " -nostdin -i " + inputVideoFileName + " -s " +
      std::to_string(downsampleFrameDimension) + ":" +
      std::to_string(downsampleFrameDimension) +
      " -an -f rawvideo -c:v rawvideo -pix_fmt rgb24 -r " +
      std::to_string(resampleFramesPerSecond) + " pipe:1";
  return hashVideo(
      downsampleFrameDimension,
      command,
      tmkFramewiseAlgorithm,
      resampleFramesPerSecond,
      tmkFeatureVectors,
      verbose,
      argv0);
}

} // namespace hashing
} // namespace tmk
} // namespace facebook
