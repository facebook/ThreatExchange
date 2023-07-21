// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <cstdlib>
#include <string>
#include <vector>

#include <vpdq/cpp/hashing/filehasher.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>
#include <vpdq/cpp/io/vpdqio.h>

static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options]\n", argv0);
  fprintf(fp, "Required:\n");
  fprintf(fp, "-i|--input-video-file-name ...\n");
  fprintf(fp, "-o|--output-hash-file-name ...\n");
  fprintf(
      fp,
      "-r|--seconds-per-hash ...:Must be a non-negative float. If it is 0, will generate every frame's hash\n");
  fprintf(fp, "Options:\n");
  fprintf(fp, "-v|--verbose: Show all hash matching information\n");
  fprintf(
      fp,
      "-d|--output-directory ...: instead of specifiying "
      "output-file name, just give a directory and the output file name will "
      "be auto-computed from the input video file name. For example, avideofile.mp4 -> output_directory>/avideofile.txt\n");
  fprintf(
      fp,
      "-s|--downsample-frame-dimension ...: The down scaling resolution for video. The input number will be the height and width of the downscaled video. For example, -s 160 -> will make video of 1080x720 to 160x160.\n");
  exit(rc);
}

/**
 *
 * Get the base name with extension of the input path
 *
 * ./dir/sub-dir/sample.txt -> sample.txt
 *
 * @param path Path of the target file
 *
 */
std::string basename(const std::string& path) {
  size_t i = path.find_last_of("\\/");
  if (i == std::string::npos) {
    return path;
  } else {
    return path.substr(i + 1);
  }
}

/**
 *
 * Strip the extension of the input filename
 *
 * .sample.txt -> sample
 *
 * @param filename Path of the target file
 *
 */
std::string stripExtension(const std::string& filename) {
  size_t n = filename.rfind('.');
  if (n == std::string::npos) {
    return filename;
  } else {
    return filename.substr(0, n);
  }
}

int main(int argc, char** argv) {
  int argi = 1;
  bool verbose = false;
  std::string inputVideoFileName = "";
  std::string outputHashFileName = "";
  std::string outputDirectory = "";
  double secondsPerHash = 0;
  int downsampleFrameDimension = 0;
  unsigned int thread_count = 0;

  while ((argi < argc) && argv[argi][0] == '-') {
    std::string flag(argv[argi++]);
    if (flag == "-v" || flag == "--verbose") {
      verbose = true;
      continue;
    }
    if (flag == "-i" || flag == "--input-video-file-name") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      inputVideoFileName = std::string(argv[argi++]);
      continue;
    }
    if (flag == "-o" || flag == "--output-hash-file-name") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      outputHashFileName = std::string(argv[argi++]);
      continue;
    }
    if (flag == "-f" || flag == "--ffmpeg-path") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      // does nothing anymore
      continue;
    }
    if (flag == "-r" || flag == "--seconds-per-hash") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      secondsPerHash = std::atof(argv[argi++]);
      continue;
    }
    if (flag == "-d" || flag == "--output-directory") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      outputDirectory = std::string(argv[argi++]);
      continue;
    }
    if (flag == "-s" || flag == "--downsample-frame-dimension") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      downsampleFrameDimension = std::atoi(argv[argi++]);
      continue;
    }
    if (flag == "-t" || flag == "--thread-count") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      thread_count = std::atoi(argv[argi++]);
      continue;
    }
    usage(argv[0], 1);
  }

  if (inputVideoFileName.empty()) {
    fprintf(stderr, "%s: --input-video-file-name missing\n", argv[0]);
    usage(argv[0], 1);
  }

  if ((outputHashFileName.empty() && outputDirectory.empty()) ||
      (!outputHashFileName.empty() && !outputDirectory.empty())) {
    fprintf(
        stderr,
        "%s: need one of --output-hash-file-name "
        "or --output-directory\n",
        argv[0]);
    usage(argv[0], 1);
  }

  if (secondsPerHash < 0) {
    fprintf(
        stderr,
        "%s: --seconds-per-hash must be a non-negative float.\n",
        argv[0]);
    usage(argv[0], 1);
  }

  // Get the output hash file name if outputDirectory is specified
  if (!outputDirectory.empty()) {
    std::string b = basename(inputVideoFileName);
    b = stripExtension(b);
    outputHashFileName = outputDirectory + "/" + b + ".txt";
  }

  // Hash the video and store the features in pdqHashes
  std::vector<facebook::vpdq::hashing::vpdqFeature> pdqHashes;

  bool rc = facebook::vpdq::hashing::hashVideoFile(
      inputVideoFileName,
      pdqHashes,
      verbose,
      secondsPerHash,
      downsampleFrameDimension,
      downsampleFrameDimension,
      thread_count);
  if (!rc) {
    fprintf(
        stderr,
        "%s: failed to hash \"%s\".\n",
        argv[0],
        inputVideoFileName.c_str());
    return EXIT_FAILURE;
  }
  facebook::vpdq::io::outputVPDQFeatureToFile(outputHashFileName, pdqHashes);
  return EXIT_SUCCESS;
}
