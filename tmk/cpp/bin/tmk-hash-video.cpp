// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

// Example:
// for v in /path/to/*.mp4; do
//   ./tmk-hash-video -f /usr/local/bin/ffmpeg -i $v -d .
// done
//
// tmk-two-level-score *.tmk | sort -n

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <iostream>
#include <memory>
#include <string>
#include <tmk/cpp/hashing/filehasher.h>

using namespace std;

const std::string PATH_SEPARATOR =
#if defined(_WIN32)
    "\\";
#else
    "/";
#endif

// ----------------------------------------------------------------
void usage(char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options]\n", argv0);
  fprintf(fp, "Required:\n");
  fprintf(fp, "-f|--ffmpeg-path ...\n");
  fprintf(fp, "-i|--input-video-file-name ...\n");
  fprintf(fp, "-o|--output-feature-vectors-file-name ...\n");
  fprintf(fp, "Optional:\n");
  fprintf(fp, "-v|--verbose\n");
  fprintf(
      fp,
      "-d|--output-directory ...: instead of specifying "
      "output-file name, just give a directory and the output file name will "
      "be auto-computed from the input video file name.\n");
  exit(exit_rc);
}

// ----------------------------------------------------------------
std::string basename(const std::string& path, const std::string& delimiter) {
  size_t n = path.length();
  size_t i = path.rfind(delimiter, n);
  if (i == string::npos) {
    return path;
  } else {
    return path.substr(i + 1, n - i);
  }
}

// ----------------------------------------------------------------
std::string stripExtension(
    const std::string& path, const std::string& delimiter) {
  size_t n = path.length();
  size_t i = path.rfind(delimiter, n);
  if (i == string::npos) {
    return path;
  } else {
    return path.substr(0, i);
  }
}

// ----------------------------------------------------------------
int main(int argc, char* argv[]) {
  int resampleFramesPerSecond = 15; // TMK default
  std::string frameFeatureAlgorithmName = "pdqf";

  bool verbose = false;
  std::string ffmpegPath = "";
  std::string inputVideoFileName = "";
  std::string outputFeatureVectorsFileName = "";
  std::string outputDirectory = "";

  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    std::string flag(argv[argi++]);

    if (flag == "=h" || flag == "--help") {
      usage(argv[0], 0);
    } else if (flag == "-v" || flag == "--verbose") {
      verbose = true;

    } else if (flag == "-f" || flag == "i--ffmpeg-path") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      ffmpegPath = std::string(argv[argi++]);

    } else if (flag == "-i" || flag == "--input-video-file-name") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      inputVideoFileName = std::string(argv[argi++]);

    } else if (flag == "-o" || flag == "--output-feature-vectors-file-name") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      outputFeatureVectorsFileName = std::string(argv[argi++]);

    } else if (flag == "-d" || flag == "--output-directory") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      outputDirectory = std::string(argv[argi++]);

    } else {
      usage(argv[0], 1);
    }
  }

  if (ffmpegPath.empty()) {
    fprintf(stderr, "%s: --ffmpeg-path missing\n", argv[0]);
    usage(argv[0], 1);
  }

  if (inputVideoFileName.empty()) {
    fprintf(stderr, "%s: --input-video-file-name missing\n", argv[0]);
    usage(argv[0], 1);
  }

  if (outputFeatureVectorsFileName.empty() && outputDirectory.empty()) {
    fprintf(
        stderr,
        "%s: need one of --output-feature-vectors-file-name "
        "or --output-directory\n",
        argv[0]);
    usage(argv[0], 1);
  }

  if (!outputFeatureVectorsFileName.empty() && !outputDirectory.empty()) {
    fprintf(
        stderr,
        "%s: need one of --output-feature-vectors-file-name "
        "or --output-directory\n",
        argv[0]);
    usage(argv[0], 1);
  }

  facebook::tmk::io::TMKFramewiseAlgorithm tmkFramewiseAlgorithm =
      facebook::tmk::io::algoFromLowercaseName(frameFeatureAlgorithmName);
  if (tmkFramewiseAlgorithm ==
      facebook::tmk::io::TMKFramewiseAlgorithm::UNRECOGNIZED) {
    fprintf(stderr, "%s: unrecognized algorithm name.\n", argv[0]);
    return 1;
  }

  facebook::tmk::algo::TMKFeatureVectors tmkFeatureVectors;
  bool rc = facebook::tmk::hashing::hashVideoFile(
      inputVideoFileName,
      tmkFramewiseAlgorithm,
      ffmpegPath,
      resampleFramesPerSecond,
      tmkFeatureVectors,
      verbose,
      argv[0]);

  if (!rc) {
    fprintf(
        stderr,
        "%s: failed to hash \"%s\".\n",
        argv[0],
        inputVideoFileName.c_str());
    return 1;
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  if (outputDirectory != "") {
    // Strip containing directory:
    std::string b = basename(inputVideoFileName, PATH_SEPARATOR);
    // Strip file extension:
    b = stripExtension(b, ".");
    // E.g. -i /path/to/foo.mp4 -d /tmp -> /tmp/foo.tmk
    outputFeatureVectorsFileName =
        outputDirectory + PATH_SEPARATOR + b + ".tmk";
  }

  FILE* outputFp = facebook::tmk::io::openFileOrDie(
      outputFeatureVectorsFileName.c_str(), "wb", argv[0]);
  if (!tmkFeatureVectors.writeToOutputStream(outputFp, argv[0])) {
    perror("fwrite");
    fprintf(
        stderr,
        "%s: could not write feature-vectors to \"%s\".\n",
        argv[0],
        outputFeatureVectorsFileName.c_str());
    return 1;
  }
  fclose(outputFp);

  if (outputDirectory != "") {
    printf(
        "%s %s\n",
        inputVideoFileName.c_str(),
        outputFeatureVectorsFileName.c_str());
  }

  return 0;
}
