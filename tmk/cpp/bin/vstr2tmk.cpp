// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Step 2 and 3 of TMK 3-stage hashing pipeline:
// * vid2vstr (or ffmpeg.exe): .mp4 file to .vstr decoded stream
// * vstr2feat: .vstr file to .feat list of frame-featue vectors
// * feat2tmk: .feat file to .tmk list of TMK cosine/sine features
// ================================================================

#include <tmk/cpp/hashing/bufferhashers.h>
#include <tmk/cpp/io/tmkio.h>
#include <tmk/cpp/algo/tmkfv.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <memory>

using namespace facebook::tmk;
using namespace facebook::tmk::algo;

// ----------------------------------------------------------------
// Status codes for video hashing shell contract
enum class VideoHashingStatus {
  OK = 0,
  FATAL = 1,
  FILE_NOT_FOUND = 4,
  TOO_SMALL = 5,
};

// ================================================================
void usage(char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options] [input file name]\n", argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "--frame-feature-algorithm-name {PDNA|PDQF|GIST}\n");
  fprintf(fp, "--output-feature-vectors-file-name {x}\n");
  fprintf(fp, "-v|--verbose\n");
  fprintf(fp, "--raw:  Without --raw, width, height, and frames per second\n");
  fprintf(fp, "  are taken from the input .vstr file header and must not\n");
  fprintf(fp, "  be specified on the command line. With --raw, the input is\n");
  fprintf(fp, "  taken to be raw RGB frame-rasters, and width/height/fps\n");
  fprintf(fp, "  must all be specified on the command line.\n");
  fprintf(fp, "--width {w}:  See --raw\n");
  fprintf(fp, "--height {h}: See --raw\n");
  fprintf(fp, "--fps {n}:    See --raw\n");
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  char* frameFeatureAlgorithmName = nullptr;
  char* outputFeatureVectorsFileName = nullptr;
  bool verbose = false;
  int specifiedFrameHeight = -1;
  int specifiedFrameWidth = -1;
  int specifiedFramesPerSecond = -1;
  bool doRawInput = false;

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Parse command line
  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);
    } else if (!strcmp(flag, "-v") || !strcmp(flag, "--verbose")) {
      verbose = true;

    } else if (!strcmp(flag, "--frame-feature-algorithm-name")) {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      frameFeatureAlgorithmName = argv[argi++];
    } else if (!strcmp(flag, "--output-feature-vectors-file-name")) {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      outputFeatureVectorsFileName = argv[argi++];

    } else if (!strcmp(flag, "--width")) {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      if (sscanf(argv[argi], "%d", &specifiedFrameWidth) != 1) {
        usage(argv[0], 1);
      }
      argi++;
    } else if (!strcmp(flag, "--height")) {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      if (sscanf(argv[argi], "%d", &specifiedFrameHeight) != 1) {
        usage(argv[0], 1);
      }
      argi++;
    } else if (!strcmp(flag, "--fps")) {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      if (sscanf(argv[argi], "%d", &specifiedFramesPerSecond) != 1) {
        usage(argv[0], 1);
      }
      argi++;
    } else if (!strcmp(flag, "--raw")) {
      doRawInput = true;

    } else {
      usage(argv[0], 1);
    }
  }

  // Check flags for consistency
  if (frameFeatureAlgorithmName == nullptr) {
    fprintf(
        stderr,
        "%s: --frame-feature-algorithm-name option is required.\n",
        argv[0]);
    usage(argv[0], 1);
  }
  if (doRawInput) {
    if (specifiedFrameHeight == -1 || specifiedFrameWidth == -1 ||
        specifiedFramesPerSecond == -1) {
      usage(argv[0], 1);
    }
  } else {
    if (specifiedFrameHeight != -1 || specifiedFrameWidth != -1 ||
        specifiedFramesPerSecond != -1) {
      usage(argv[0], 1);
    }
  }

  io::TMKFramewiseAlgorithm algorithm =
      io::algoFromLowercaseName(frameFeatureAlgorithmName);
  if (algorithm == io::TMKFramewiseAlgorithm::UNRECOGNIZED) {
    fprintf(
        stderr,
        "%s: unrecognized algorithm name \"%s\".\n",
        argv[0],
        frameFeatureAlgorithmName);
    exit(1);
  }

  if (outputFeatureVectorsFileName == nullptr) {
    usage(argv[0], 1);
  }
  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Open the input stream. If it's raw then we already have width/height/FPS
  // parameters from the command line. Else they are contained within the file
  // header. Also open the output stream.

  FILE* inputFp = stdin;
  char* inputStreamFileName = (char*)"(stdin)";
  if ((argc - argi) == 0) {
    // keep stdin
  } else if ((argc - argi) == 1) {
    inputStreamFileName = argv[argi];
    inputFp =
        facebook::tmk::io::openFileOrDie(inputStreamFileName, "rb", argv[0]);
  } else {
    usage(argv[0], 1);
  }

  FILE* outputFp = facebook::tmk::io::openFileOrDie(
      outputFeatureVectorsFileName, "wb", argv[0]);

  // ----------------------------------------------------------------
  // Get input dimensions. Within Facebook we will use vid2vstr.c
  // which writes a .vstr file. Outside, we will use ffmpeg.exe
  // with arguments such as
  //
  //   output_width=256
  //   output_height=256
  //   output_fps=15
  //   ffmpeg -i "$1" \
  //     -s ${output_width}:${output_height} -an -f rawvideo -c:v rawvideo \
  //       -pix_fmt bgr24 -r $output_fps pipe:1
  //
  // which writes raw RGB frame-rasters. (Same as .vstr file without the
  // header.)

  int frameHeight = specifiedFrameHeight;
  int frameWidth = specifiedFrameWidth;
  int framesPerSecond = specifiedFramesPerSecond;
  if (!doRawInput) {
    io::DecodedVideoStreamFileHeader vstrHeader;
    bool rc = facebook::tmk::io::readDecodedVideoStreamFileHeader(
        inputFp, &vstrHeader, argv[0]);
    if (!rc) {
      fprintf(
          stderr,
          "%s: could not read .vstr header from \"%s\".\n",
          argv[0],
          inputStreamFileName);
      exit(1);
    }
    frameHeight = vstrHeader.frameHeight;
    frameWidth = vstrHeader.frameWidth;
    framesPerSecond = vstrHeader.framesPerSecond;
  }

  if (verbose) {
    fprintf(stderr, "%s: %s ENTER\n", argv[0], inputStreamFileName);
    fprintf(stderr, "frameHeight      %d\n", frameHeight);
    fprintf(stderr, "frameWidth       %d\n", frameWidth);
    fprintf(stderr, "framesPerSecond %d\n", framesPerSecond);
  }

  // ----------------------------------------------------------------
  std::unique_ptr<hashing::AbstractFrameBufferHasher> phasher =
      hashing::FrameBufferHasherFactory::createFrameHasher(
          algorithm, frameHeight, frameWidth);

  int frameFeatureDimension = phasher->getFeatureDimension();

  // ----------------------------------------------------------------
  // Allocate this and re-use it over frames, rather than allocating/freeing
  // on each frame.
  std::unique_ptr<uint8_t[]> rawFrameBuffer(
      new uint8_t[frameHeight * frameWidth * 3]);
  std::vector<float> feature(frameFeatureDimension);

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  std::vector<int> periods =
      facebook::tmk::algo::TMKFeatureVectors::makePoullotPeriods();

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // TODO(t25190142): run the Baraldi Python code and learn optimal
  // coefficients.
  std::vector<float> fourierCoefficients =
      facebook::tmk::algo::TMKFeatureVectors::makePoullotFourierCoefficients();

  facebook::tmk::algo::TMKFeatureVectors tmkFeatureVectors(
      algorithm,
      framesPerSecond,
      periods,
      fourierCoefficients,
      frameFeatureDimension);

  bool eof = false;
  while (!feof(inputFp)) {
    bool read_rc = facebook::tmk::io::readRGBTriples(
        rawFrameBuffer.get(), frameHeight, frameWidth, inputFp, eof);
    if (eof) {
      break;
    }
    if (!read_rc) {
      perror("fread");
      fprintf(
          stderr,
          "%s: failed to read frame buffer %d.\n",
          argv[0],
          tmkFeatureVectors.getFrameFeatureCount());
      return (int)VideoHashingStatus::FATAL;
    }
    if (verbose) {
      if ((tmkFeatureVectors.getFrameFeatureCount() % 100) == 0) {
        fprintf(
            stderr,
            "%s: frame %d\n",
            argv[0],
            tmkFeatureVectors.getFrameFeatureCount());
      }
    }

    if (!phasher->hashFrame(rawFrameBuffer.get(), feature)) {
      fprintf(
          stderr,
          "%s: failed to hash frame buffer %d.\n",
          argv[0],
          tmkFeatureVectors.getFrameFeatureCount());
      return (int)VideoHashingStatus::FATAL;
    }

    tmkFeatureVectors.ingestFrameFeature(
        feature, tmkFeatureVectors.getFrameFeatureCount());
  }

  tmkFeatureVectors.finishFrameFeatureIngest();

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  if (!tmkFeatureVectors.writeToOutputStream(outputFp, argv[0])) {
    perror("fwrite");
    fprintf(stderr, "%s: could not write feature-vectors.\n", argv[0]);
    return 1;
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  fclose(outputFp);

  return 0;
}
