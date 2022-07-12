#include <vector>
#include <vpdq/cpp/hashing/filehasher.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>
#include <vpdq/cpp/io/vpdqio.h>

using namespace std;

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
  fprintf(fp, "-f|--ffmpeg-path: Specific path to ffmpeg you want to use\n");
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

// TODO: Move to a shared library
// Directly copy from TMK
/**
 *
 * Get the base name with extension of the input path
 *
 * ./dir/sub-dir/sample.txt -> sample.txt
 *
 * @param path Path of the target file
 * @param delimiter The character that marks the beginning or end
 *
 */
string basename(const string& path, const string& delimiter) {
  size_t n = path.length();
  size_t i = path.rfind(delimiter, n);
  if (i == string::npos) {
    return path;
  } else {
    return path.substr(i + 1, n - i);
  }
}

/**
 *
 * Stip the extension of the input path
 *
 * .sample.txt -> sample
 *
 * @param path Path of the target file
 * @param delimiter The character that marks the beginning or end
 *
 */
string stripExtension(const string& path, const string& delimiter) {
  size_t n = path.length();
  size_t i = path.rfind(delimiter, n);
  if (i == string::npos) {
    return path;
  } else {
    return path.substr(0, i);
  }
}

int main(int argc, char** argv) {
  int argi = 1;
  bool verbose = false;
  string ffmpegPath = "ffmpeg";
  string inputVideoFileName = "";
  string outputHashFileName = "";
  string outputDirectory = "";
  double secondsPerHash = 0;
  int downsampleFrameDimension = 0;

  while ((argi < argc) && argv[argi][0] == '-') {
    string flag(argv[argi++]);
    if (flag == "-v" || flag == "--verbose") {
      verbose = true;
      continue;
    }
    if (flag == "-i" || flag == "--input-video-file-name") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      inputVideoFileName = string(argv[argi++]);
      continue;
    }
    if (flag == "-o" || flag == "--output-hash-file-name") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      outputHashFileName = string(argv[argi++]);
      continue;
    }
    if (flag == "-f" || flag == "--ffmpeg-path") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      ffmpegPath = string(argv[argi++]);
      continue;
    }
    if (flag == "-r" || flag == "--seconds-per-hash") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      secondsPerHash = atof(argv[argi++]);
      continue;
    }
    if (flag == "-d" || flag == "--output-directory") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      outputDirectory = string(argv[argi++]);
      continue;
    }
    if (flag == "-s" || flag == "--downsample-frame-dimension") {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      downsampleFrameDimension = atoi(argv[argi++]);
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

  if (outputDirectory != "") {
    // Strip containing directory:
    std::string b = basename(inputVideoFileName, "/");
    // Strip file extension:
    b = stripExtension(b, ".");
    outputHashFileName = outputDirectory + "/" + b + ".txt";
  }
  // Hash the video and store the hashes and correspoding info
  double framesPerSec = 0;
  int videoWidth = 0;
  int videoHeight = 0;
  bool rc = facebook::vpdq::io::readVideoStreamInfo(
      inputVideoFileName, videoWidth, videoHeight, framesPerSec, argv[0]);
  if (!rc) {
    fprintf(
        stderr,
        "%s: failed to read video stream information\"%s\".\n",
        argv[0],
        inputVideoFileName.c_str());
    return 1;
  }
  std::vector<facebook::vpdq::hashing::vpdqFeature> pdqHashes;
  int width = downsampleFrameDimension;
  int height = downsampleFrameDimension;
  if (downsampleFrameDimension == 0) {
    width = videoWidth;
    height = videoHeight;
  }

  rc = facebook::vpdq::hashing::hashVideoFile(
      inputVideoFileName,
      pdqHashes,
      ffmpegPath,
      verbose,
      secondsPerHash,
      width,
      height,
      framesPerSec,
      argv[0]);
  if (!rc) {
    fprintf(
        stderr,
        "%s: failed to hash \"%s\".\n",
        argv[0],
        inputVideoFileName.c_str());
    return 1;
  }
  facebook::vpdq::io::outputVPDQFeatureToFile(
      outputHashFileName, pdqHashes, argv[0]);
  return 0;
}
