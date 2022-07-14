#include <pdq/cpp/common/pdqhashtypes.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>

#ifndef FILEHASHER_H
#define FILEHASHER_H

using namespace std;

namespace facebook {
namespace vpdq {
namespace hashing {

/**
 * Get frames by passing video file through ffmpeg
 * Then get pdq hashes for selected frames every secondPerHash
 *
 * @param inputVideoFileName Input video's name
 * @param pdqHashes Vector which stores hashes
 * @param ffmpegPath Ffmpeg's path
 * @param verbose If produce detailed output for diagnostic purposes
 * @param secondsPerHash The time period of picking frames in vpdq
 * @param width Specified width of the input video
 * @param height Specified height of the input video
 * @param framesPerSec Frames per second of the input video
 * @param downsampleFrameDimension The down-scale dimensions for vpdq
 * @param programName The name of executable program which invokes the function
 *
 * @return If successfully hash the video
 */

bool hashVideoFile(
    const std::string& inputVideoFileName,
    vector<hashing::vpdqFeature>& pdqHashes,
    const std::string& ffmpegPath,
    bool verbose,
    const double secondsPerHash,
    const int width,
    const int height,
    const double framesPerSec,
    const char* programName);
} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // FILEHASHER_H
