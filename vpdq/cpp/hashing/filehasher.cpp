#include <math.h>
#include <stdio.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <vpdq/cpp/hashing/bufferhasher.h>
#include <vpdq/cpp/hashing/filehasher.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>

using namespace std;

namespace facebook {
namespace vpdq {
namespace hashing {

/**
 * Get frames by passing video file through ffmpeg
 * Then get pdq hashes for selected frames every secondsPerHash
 * The return boolean represents whether the hashing process is successful or
 *not.
 **/

bool hashVideoFile(
    const string& inputVideoFileName,
    vector<hashing::vpdqFeature>& pdqHashes,
    const string& ffmpegPath,
    bool verbose,
    const double secondsPerHash,
    const int width,
    const int height,
    const double framesPerSec,
    const char* argv0) {
  stringstream ss;

  ss << quoted(inputVideoFileName);
  string escapedInputVideoFileName = ss.str();
  // FFMPEG command to process the downsampled video

  string ffmpegLogLevel =
      verbose ? "" : "-loglevel warning -hide_banner -stats";
  string command = ffmpegPath + " " + ffmpegLogLevel + " -nostdin -i " +
      escapedInputVideoFileName + " -s " + to_string(width) + ":" +
      to_string(height) + " -an -f rawvideo -c:v rawvideo -pix_fmt rgb24" +
      " pipe:1";
  FILE* inputFp = popen(command.c_str(), "r");
  if (inputFp == nullptr) {
    fprintf(stderr, "%s: ffmpeg to generate video stream failed\n", argv0);
    return false;
  }

  bool eof = false;

  // Create the PDQ Frame Buffer Hasher
  std::unique_ptr<vpdq::hashing::AbstractFrameBufferHasher> phasher =
      vpdq::hashing::FrameBufferHasherFactory::createFrameHasher(height, width);
  if (phasher == nullptr) {
    fprintf(stderr, "Error: Phasher is null");
    return false;
  }

  // Create a Frame Buffer to reuse everytime for hashing
  int numRGBTriples = height * width;
  int fno = 0;
  unique_ptr<uint8_t[]> rawFrameBuffer(new uint8_t[numRGBTriples * 3]);
  // Intentional floor operation calculate frameMod as an integer
  int frameMod = secondsPerHash * framesPerSec;
  if (frameMod == 0) {
    // Avoid truncate to zero on corner-case with secondsPerHash = 1
    // and framesPerSec < 1.
    frameMod = 1;
  }
  // Loop through the video frames
  while (!feof(inputFp)) {
    size_t fread_rc = fread(rawFrameBuffer.get(), 3, numRGBTriples, inputFp);
    if (fread_rc == 0) {
      eof = true;
    }
    if (eof) {
      break;
    }
    pdq::hashing::Hash256 pdqHash;
    if (fno % frameMod == 0) {
      if (verbose) {
        printf("selectframe %d\n", fno);
      }
      // Call pdqHasher to hash the frame
      int quality;
      if (!phasher->hashFrame(rawFrameBuffer.get(), pdqHash, quality)) {
        fprintf(
            stderr,
            "%s: failed to hash frame buffer. Frame width or height smaller than minimum hashable dimension. %d.\n",
            argv0,
            fno);
        return false;
      }
      // Push to pdqHashes vector
      pdqHashes.push_back({pdqHash, fno, quality, (double)fno / framesPerSec});
      if (verbose) {
        printf("PDQHash: %s \n", pdqHash.format().c_str());
      }
    }
    fno++;
    if (fread_rc != numRGBTriples) {
      perror("fread");
      fprintf(
          stderr,
          "Expected %d RGB triples; got %d\n",
          numRGBTriples,
          (int)fread_rc);
    }
  }
  return true;
}

} // namespace hashing
} // namespace vpdq
} // namespace facebook
