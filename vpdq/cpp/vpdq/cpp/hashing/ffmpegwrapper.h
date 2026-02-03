// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef VPDQ_HASHING_FFMPEGWRAPPER_H
#define VPDQ_HASHING_FFMPEGWRAPPER_H

#include <vpdq/cpp/hashing/ffmpegwrapper.h>

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/frame.h>
#include <libswscale/swscale.h>
}

namespace facebook {
namespace vpdq {
namespace hashing {
namespace ffmpeg {

/**
 * @brief Pixel format for the image passed to PDQ
 *
 * @note
 * This shouldn't be changed unless PDQ expects a different pixel format.
 */
constexpr AVPixelFormat get_pixel_format() {
  return AV_PIX_FMT_RGB24;
}

/**
 * @brief Downsample method for the image passed to PDQ.
 *
 * @note
 * Changing this may affect performance and will almost certainly affect the
 * output perceptual hash of the frame.
 */
constexpr int get_downsample_method() {
  return SWS_AREA;
}

// Custom deleters used to wrap FFmpeg objects with smart pointers

/** @brief A custom deleter functor for AVFrame* */
struct AVFrameDeleter {
  void operator()(AVFrame* ptr) const;
};

/** @brief A custom deleter functor for AVPacket* */
struct AVPacketDeleter {
  void operator()(AVPacket* ptr) const;
};

/** @brief A custom deleter functor for SwsContext* */
struct SwsContextDeleter {
  void operator()(SwsContext* ptr) const;
};

/** @brief A custom deleter functor for AVFormatContext* */
struct AVFormatContextDeleter {
  void operator()(AVFormatContext* ptr) const;
};

/** @brief A custom deleter functor for AVCodecContext* */
struct AVCodecContextDeleter {
  void operator()(AVCodecContext* ptr) const;
};

/** @brief A smart pointer wrapper for AVFrame */
using AVFramePtr = std::unique_ptr<AVFrame, AVFrameDeleter>;

/** @brief A smart pointer wrapper for AVPacket */
using AVPacketPtr = std::unique_ptr<AVPacket, AVPacketDeleter>;

/** @brief A smart pointer wrapper for SwsContext */
using SwsContextPtr = std::unique_ptr<SwsContext, SwsContextDeleter>;

/** @brief A smart pointer wrapper for AVFormatContext */
using AVFormatContextPtr =
    std::unique_ptr<AVFormatContext, AVFormatContextDeleter>;

/** @brief A smart pointer wrapper for AVCodecContext */
using AVCodecContextPtr =
    std::unique_ptr<AVCodecContext, AVCodecContextDeleter>;

/** @brief Video wrapper that can open a video file. */
class FFmpegVideo {
 public:
  FFmpegVideo(const std::string& filename);

  /**
   * @brief Create the SwsContext for resizing the video frames.
   *
   * @return True if the swscontext was successfully created, otherwise false.
   *
   * @note If the SwsContext fails to be created then swsContext will be
   * nullptr.
   */
  bool createSwsContext();

  // Copy
  FFmpegVideo(const FFmpegVideo&) = delete;
  FFmpegVideo& operator=(const FFmpegVideo&) = delete;

  // Move
  FFmpegVideo(FFmpegVideo&&) = default;
  FFmpegVideo& operator=(FFmpegVideo&&) = default;

  ~FFmpegVideo() = default;

  AVCodecContextPtr codecContext;
  AVFormatContextPtr formatContext;
  SwsContextPtr swsContext;
  unsigned int videoStreamIndex;
  int width;
  int height;
  double frameRate;
};

/** @brief AVFrame implementation of the Frame type class. */
class FFmpegFrame {
 public:
  /** @brief Constructor
   *
   *  @param frame The AVFrame.
   *  @param frameNumber The frame number in the video.
   *  @param linesize The number of bytes per row in the buffer including
   *  padding.
   **/
  FFmpegFrame(AVFramePtr frame, uint64_t frameNumber, int linesize);

  /** @brief Get the frame number.
   *
   *  @return The frame number.
   **/
  uint64_t get_frame_number() const;

  /** @brief Get the pointer to the frame data buffer to be used for hashing. */
  unsigned char* get_buffer_ptr();

  /** @brief Get the linesize of the frame buffer. */
  int get_linesize() const;

  // Copy
  FFmpegFrame(const FFmpegFrame&) = delete;
  FFmpegFrame& operator=(const FFmpegFrame&) = delete;

  // Move
  FFmpegFrame(FFmpegFrame&&) = default;
  FFmpegFrame& operator=(FFmpegFrame&&) = default;

  ~FFmpegFrame() = default;

 private:
  AVFramePtr m_frame;
  uint64_t m_frameNumber;
  int m_linesize;
};

/** @brief Writes a raw AVFrame to a file (used for debugging only).
 *
 * @param frame The frame to write. Must not be nullptr and its data must not be
 *              nullptr.
 * @param filename Name of output file.
 *
 * @note The output frame can viewed using ffplay directly:
 *
 * ffplay -f rawvideo -pixel_format rgb24 video_size <width>x<height> <filename>
 *
 **/
void saveFrameToFile(AVFramePtr frame, const std::string& filename);

/** @brief Creates an RGB24 AVFrame.
 *
 * @param width Width of the resulting frame.
 * @param height Height of the resulting frame.
 * @return The RGB24 frame.
 **/
AVFramePtr createRGB24Frame(size_t width, size_t height);

} // namespace ffmpeg
} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // VPDQ_HASHING_FFMPEGWRAPPER_H
